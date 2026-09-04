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
"""A sign-off request that has nowhere to go yet — queued rather than lost.

Revoking a granted sign-off used to live here too. It was removed: a committee
decision is not unsigned, and a rating changes by re-classifying the model, which
moves the heatmap and sends the new cell to the MRC on its own.
"""
from __future__ import annotations

from tests.web import test_mrc_signoff_api as ms
from tests.web import test_product_signoff_api as ps
from tests.web.conftest import HEADERS














def test_model_pending_signoff_queued_without_meeting(client):
    ms._seed_mrc(client)
    ms._register_subject_model(client)
    ms._request_signoff(client)          # queued — no meeting to attach to
    pending = client.get("/api/models/M1/risk-rating").get_json()["pending_signoff"]
    assert pending["status"] == "Pending"
    assert "meeting_id" not in pending   # the Attached-only fields are omitted










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


def test_a_decision_about_a_subject_that_is_no_longer_there_is_404(client):
    """The agenda item is a pointer, and the log it points into is append-only —
    so an item can outlive what it named. The committee is told, rather than the
    decision being recorded against nothing."""
    ms._seed_mrc(client)
    ms._schedule_meeting(client)
    added = client.post("/api/meetings/MTG1/collections/agenda",
                        json={"fields": {"title": "Ratify the rating",
                                         "subject_product_id": "GHOST",
                                         "signoff_kind": "rag",
                                         "proposed_rag": "Green"},
                              "confirmed": True}, headers=HEADERS)
    item = [a for a in added.get_json()["data"]["agenda"] if a.get("title") == "Ratify the rating"][0]
    item_id = item["item_id"]
    refused = client.post(
        f"/api/meetings/MTG1/agenda/{item_id}/approve-signoff",
        json={"confirmed": True}, headers=HEADERS)
    assert refused.status_code == 404
    assert "GHOST" in refused.get_json()["error"]
