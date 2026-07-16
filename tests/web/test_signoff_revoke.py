# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Revoking a granted sign-off (model + product) and the queued-pending branch."""
from __future__ import annotations

from tests.web import test_mrc_signoff_api as ms
from tests.web import test_product_signoff_api as ps
from tests.web.conftest import HEADERS


def _approve(client, agenda_id):
    return client.post(f"/api/meetings/MTG1/agenda/{agenda_id}/approve-signoff",
                       json={"confirmed": True}, headers=HEADERS)


def _sign_off_model(client):
    ms._seed_mrc(client)
    # tier 1 × Low × Low → heatmap Green; propose (and approve) Green so the
    # approved rating matches the heatmap and the model reads as signed off.
    ms._register_subject_model(client, tier=1, materiality="Low", complexity="Low")
    ms._schedule_meeting(client)
    ms._request_signoff(client)                  # proposes Green
    _approve(client, ms._signoff_item(client)["item_id"])


def _sign_off_product(client):
    ps._seed_mrc(client)
    ps._model(client)
    ps._product(client, rag="Green", tier=1, materiality="Low", complexity="Low")
    ps._schedule(client)
    ps._request(client)                          # proposes the current Green rating
    _approve(client, ps._signoff_items(client)[0]["item_id"])


# --- model revoke -----------------------------------------------------------

def test_model_revoke_succeeds_after_signoff(client):
    _sign_off_model(client)
    resp = client.post("/api/models/M1/revoke-signoff", json={"confirmed": True}, headers=HEADERS)
    assert resp.status_code == 200
    # The rating is kept but no longer approved.
    assert client.get("/api/models/M1/risk-rating").get_json()["signed_off"] is False


def test_model_revoke_requires_confirmation(client):
    _sign_off_model(client)
    assert client.post("/api/models/M1/revoke-signoff", json={}, headers=HEADERS).status_code == 409


def test_model_revoke_unknown_is_404(client):
    resp = client.post("/api/models/NOPE/revoke-signoff", json={"confirmed": True}, headers=HEADERS)
    assert resp.status_code == 404


def test_model_revoke_when_not_signed_off_is_400(client):
    ms._register_subject_model(client)
    resp = client.post("/api/models/M1/revoke-signoff", json={"confirmed": True}, headers=HEADERS)
    assert resp.status_code == 400
    assert "not currently signed off" in resp.get_json()["error"]


def test_model_pending_signoff_queued_without_meeting(client):
    ms._seed_mrc(client)
    ms._register_subject_model(client)
    ms._request_signoff(client)          # queued — no meeting to attach to
    pending = client.get("/api/models/M1/risk-rating").get_json()["pending_signoff"]
    assert pending["status"] == "Pending"
    assert "meeting_id" not in pending   # the Attached-only fields are omitted


# --- product revoke ---------------------------------------------------------

def test_product_revoke_succeeds_after_signoff(client):
    _sign_off_product(client)
    resp = client.post("/api/products/P1/revoke-signoff", json={"confirmed": True}, headers=HEADERS)
    assert resp.status_code == 200


def test_product_revoke_requires_confirmation(client):
    _sign_off_product(client)
    assert client.post("/api/products/P1/revoke-signoff", json={}, headers=HEADERS).status_code == 409


def test_product_revoke_unknown_is_404(client):
    resp = client.post("/api/products/NOPE/revoke-signoff", json={"confirmed": True}, headers=HEADERS)
    assert resp.status_code == 404


def test_product_revoke_when_not_signed_off_is_400(client):
    ps._seed_mrc(client)
    ps._model(client)
    ps._product(client)
    resp = client.post("/api/products/P1/revoke-signoff", json={"confirmed": True}, headers=HEADERS)
    assert resp.status_code == 400
    assert "not currently signed off" in resp.get_json()["error"]


def test_product_mrc_unknown_is_404(client):
    assert client.get("/api/products/NOPE/mrc").status_code == 404


def test_product_request_signoff_unknown_is_404(client):
    resp = client.post("/api/products/NOPE/request-signoff", json={"confirmed": True}, headers=HEADERS)
    assert resp.status_code == 404


def test_product_mrc_surfaces_pending_without_meeting(client):
    ps._seed_mrc(client)
    ps._model(client)
    ps._product(client)
    ps._request(client)                  # queued — no meeting
    pending = client.get("/api/products/P1/mrc").get_json()["pending_signoff"]
    assert pending["status"] == "Pending"
    assert "meeting_id" not in pending
