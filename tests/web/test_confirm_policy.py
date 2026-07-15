# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Confirm-to-amend policy: only important changes still require confirmation
(register model/product, retire product, owner/risk changes, meeting Status, and
MRC sign-off / reject / revoke). Everything else applies without confirmation."""
from __future__ import annotations

from tests.web.conftest import HEADERS
from tests.web.test_mrc_signoff_api import (
    _register_subject_model,
    _request_signoff,
    _schedule_meeting,
    _seed_mrc,
    _signoff_item,
)


def _model(client, model_id="M1"):
    return client.post("/api/models", json={
        "model_id": model_id, "name": "Alpha",
        "fields": {"rag_rating": "Amber"}, "confirmed": True}, headers=HEADERS)


def _product(client, product_id="P1"):
    _model(client)
    return client.post("/api/products", json={
        "product_id": product_id, "product": "Bond",
        "fields": {"analytics_model": "M1", "market_data_model": "m",
                   "calculating_agent": "c"}, "confirmed": True}, headers=HEADERS)


def _field(client, path, field, value, confirmed=False):
    body = {"field": field, "value": value}
    if confirmed:
        body["confirmed"] = True
    return client.post(path, json=body, headers=HEADERS)


# --- critical commands: registration + retire still require confirmation ---

def test_register_model_requires_confirmation(client):
    r = client.post("/api/models", json={"model_id": "M1", "name": "Alpha"}, headers=HEADERS)
    assert r.status_code == 409 and r.get_json()["needs_confirmation"] is True


def test_register_product_requires_confirmation(client):
    _model(client)
    r = client.post("/api/products", json={
        "product_id": "P1", "product": "Bond",
        "fields": {"analytics_model": "M1", "market_data_model": "m",
                   "calculating_agent": "c"}}, headers=HEADERS)
    assert r.status_code == 409


def test_retire_product_requires_confirmation(client):
    _product(client)
    assert client.post("/api/products/P1/retire", json={}, headers=HEADERS).status_code == 409


# --- critical fields: owner + risk rating still require confirmation ---

def test_model_owner_change_requires_confirmation(client):
    _model(client)
    assert _field(client, "/api/models/M1/field", "owner", "carol").status_code == 409
    assert _field(client, "/api/models/M1/field", "owner", "carol", confirmed=True).status_code == 200


def test_model_rag_change_requires_confirmation(client):
    _model(client)
    assert _field(client, "/api/models/M1/field", "rag_rating", "Green").status_code == 409


def test_product_owner_and_rag_changes_require_confirmation(client):
    _product(client)
    assert _field(client, "/api/products/P1/field", "owner", "dana").status_code == 409
    assert _field(client, "/api/products/P1/field", "rag_rating", "Green").status_code == 409


# --- non-critical fields apply immediately, no confirmation ---

def test_noncritical_model_field_applies_without_confirmation(client):
    _model(client)
    r = _field(client, "/api/models/M1/field", "methodology", "Monte Carlo")
    assert r.status_code == 200
    assert r.get_json()["data"]["methodology"] == "Monte Carlo"


def test_noncritical_product_field_applies_without_confirmation(client):
    _product(client)
    r = _field(client, "/api/products/P1/field", "notes", "reviewed")
    assert r.status_code == 200
    assert r.get_json()["data"]["notes"] == "reviewed"


def test_meeting_status_is_gated_but_other_meeting_fields_are_not(client):
    _seed_mrc(client)
    _schedule_meeting(client)
    # A non-critical meeting field applies silently...
    assert _field(client, "/api/meetings/MTG1/field", "location", "Room 2").status_code == 200
    # ...but the meeting's Status is significant and still confirms.
    assert _field(client, "/api/meetings/MTG1/field", "status", "Completed").status_code == 409


# --- composed MRC decisions still require confirmation ---

def _attached_signoff(client):
    _seed_mrc(client)
    _register_subject_model(client)
    _schedule_meeting(client)
    _request_signoff(client)
    return _signoff_item(client)["item_id"]


def test_signoff_approve_requires_confirmation(client):
    aid = _attached_signoff(client)
    r = client.post(f"/api/meetings/MTG1/agenda/{aid}/approve-signoff", json={}, headers=HEADERS)
    assert r.status_code == 409


def test_signoff_reject_requires_confirmation(client):
    aid = _attached_signoff(client)
    r = client.post(f"/api/meetings/MTG1/agenda/{aid}/reject-signoff", json={}, headers=HEADERS)
    assert r.status_code == 409

# Revoke-signoff uses the same require_confirmation gate (covered above via
# approve/reject); its confirmed path is exercised by the revoke tests in
# test_models_signoff / test_product_signoff.
