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
"""Tests for the MRC sign-off actions (request / approve / escalate)."""
from __future__ import annotations

from tests.web.conftest import HEADERS


def _schedule(client, meeting_id="MTG1"):
    return client.post(
        "/api/meetings",
        json={"meeting_id": meeting_id, "title": "Q2 MRC", "date": "2026-06-30", "confirmed": True},
        headers=HEADERS,
    )


def _add(client, collection, fields):
    return client.post(
        "/api/meetings/MTG1/collections/" + collection,
        json={"fields": fields, "confirmed": True}, headers=HEADERS,
    )


def _schedule_meeting(client, meeting_id="MTG1"):
    return client.post(
        "/api/meetings",
        json={"meeting_id": meeting_id, "title": "Q3", "date": "2026-09-15", "confirmed": True},
        headers=HEADERS,
    )


def _register_subject_model(client, model_id="M1", **fields):
    return client.post(
        "/api/models",
        json={"model_id": model_id, "name": "Subject",
              "fields": {"rag_rating": "Amber", **fields}, "confirmed": True},
        headers=HEADERS,
    )


def _request_signoff(client, model_id="M1", meeting_id="MTG1", proposed_rag="Green"):
    return client.post(
        f"/api/models/{model_id}/request-signoff",
        json={"meeting_id": meeting_id, "proposed_rag": proposed_rag, "confirmed": True},
        headers=HEADERS,
    )


def test_request_signoff_adds_agenda_item(client):
    _register_subject_model(client)
    _schedule_meeting(client)
    response = _request_signoff(client)
    assert response.status_code == 201
    agenda = client.get("/api/meetings/MTG1").get_json()["data"]["agenda"]
    assert len(agenda) == 1
    assert agenda[0]["subject_model_id"] == "M1"
    assert agenda[0]["proposed_rag"] == "Green"
    assert agenda[0]["status"] == "Pending"


def test_request_signoff_rejects_missing_meeting(client):
    _register_subject_model(client)
    response = _request_signoff(client, meeting_id="NOPE")
    assert response.status_code == 404


def test_request_signoff_rejects_unknown_model(client):
    _schedule_meeting(client)
    response = _request_signoff(client, model_id="NOPE")
    assert response.status_code == 404


def test_request_signoff_requires_fields(client):
    _register_subject_model(client)
    _schedule_meeting(client)
    response = client.post(
        "/api/models/M1/request-signoff",
        json={"meeting_id": "MTG1", "confirmed": True}, headers=HEADERS,
    )
    assert response.status_code == 400


def test_request_signoff_rejects_completed_meeting(client):
    _register_subject_model(client)
    _schedule_meeting(client)
    client.post(
        "/api/meetings/MTG1/field",
        json={"field": "status", "value": "Completed", "confirmed": True}, headers=HEADERS,
    )
    response = _request_signoff(client)
    assert response.status_code == 400
    assert "Scheduled" in response.get_json()["error"]


def test_approve_signoff_snaps_model_rating_and_records_history(client):
    _register_subject_model(client)  # Amber
    _schedule_meeting(client)
    _request_signoff(client)  # proposes Green
    agenda_id = client.get("/api/meetings/MTG1").get_json()["data"]["agenda"][0]["item_id"]
    response = client.post(
        f"/api/meetings/MTG1/agenda/{agenda_id}/approve-signoff",
        json={"confirmed": True, "note": "MRC signed off after review"}, headers=HEADERS,
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["model"]["data"]["rag_rating"] == "Green"
    history = payload["model"]["data"]["rag_signoff_history"]
    assert len(history) == 1 and history[0]["from_rating"] == "Amber" and history[0]["to_rating"] == "Green"
    # The agenda item is now marked Completed.
    assert payload["meeting"]["data"]["agenda"][0]["status"] == "Completed"


def test_approve_signoff_unknown_meeting_is_404(client):
    response = client.post(
        "/api/meetings/NOPE/agenda/AG-001/approve-signoff",
        json={"confirmed": True}, headers=HEADERS,
    )
    assert response.status_code == 404


def test_approve_signoff_unknown_agenda_is_404(client):
    _schedule_meeting(client)
    response = client.post(
        "/api/meetings/MTG1/agenda/AG-999/approve-signoff",
        json={"confirmed": True}, headers=HEADERS,
    )
    assert response.status_code == 404


def test_approve_signoff_rejects_non_signoff_agenda(client):
    _schedule_meeting(client)
    _add(client, "agenda", {"title": "Regular agenda item"})
    response = client.post(
        "/api/meetings/MTG1/agenda/AG-001/approve-signoff",
        json={"confirmed": True}, headers=HEADERS,
    )
    assert response.status_code == 400
    assert "sign-off request" in response.get_json()["error"]


def test_pending_signoff_surfaces_on_risk_rating(client):
    _register_subject_model(client)
    _schedule_meeting(client)
    _request_signoff(client)
    payload = client.get("/api/models/M1/risk-rating").get_json()
    assert payload["pending_signoff"]["proposed_rag"] == "Green"
    assert payload["pending_signoff"]["meeting_id"] == "MTG1"


def test_pending_signoff_is_none_without_request(client):
    _register_subject_model(client)
    payload = client.get("/api/models/M1/risk-rating").get_json()
    assert payload["pending_signoff"] is None


# --- Phase MRC-4: escalate a sign-off to a parent MRC's meeting -------------

def _seed_signoff_ready(client, meeting_id="MTG1", parent_id="MTG2"):
    """Register a subject model, schedule two meetings, request a sign-off
    on the first. Returns the agenda item id."""
    _register_subject_model(client)
    _schedule(client, meeting_id)
    client.post(
        "/api/meetings",
        json={"meeting_id": parent_id, "title": "Parent MRC",
              "date": "2026-10-15", "confirmed": True},
        headers=HEADERS,
    )
    _request_signoff(client, model_id="M1", meeting_id=meeting_id)
    agenda = client.get(f"/api/meetings/{meeting_id}").get_json()["data"]["agenda"]
    return agenda[0]["item_id"]


def test_escalate_signoff_copies_item_to_parent_meeting(client):
    agenda_id = _seed_signoff_ready(client)
    response = client.post(
        f"/api/meetings/MTG1/agenda/{agenda_id}/escalate-signoff",
        json={"parent_meeting_id": "MTG2", "confirmed": True}, headers=HEADERS,
    )
    assert response.status_code == 200
    payload = response.get_json()
    # Original marked Escalated.
    original = payload["meeting"]["data"]["agenda"][0]
    assert original["status"] == "Escalated"
    # Parent gained a Pending sign-off item with the same subject_model_id +
    # proposed_rag, back-pointing to the original.
    parent_agenda = payload["parent"]["data"]["agenda"]
    assert len(parent_agenda) == 1
    new_item = parent_agenda[0]
    assert new_item["status"] == "Pending"
    assert new_item["subject_model_id"] == "M1"
    assert new_item["proposed_rag"] == "Green"
    assert new_item["escalated_from_meeting_id"] == "MTG1"
    assert new_item["escalated_from_agenda_id"] == agenda_id


def test_escalate_signoff_requires_parent_meeting_id(client):
    agenda_id = _seed_signoff_ready(client)
    response = client.post(
        f"/api/meetings/MTG1/agenda/{agenda_id}/escalate-signoff",
        json={"confirmed": True}, headers=HEADERS,
    )
    assert response.status_code == 400
    assert "parent_meeting_id" in response.get_json()["error"]


def test_escalate_signoff_unknown_meeting_is_404(client):
    response = client.post(
        "/api/meetings/NOPE/agenda/AG-001/escalate-signoff",
        json={"parent_meeting_id": "MTG2", "confirmed": True}, headers=HEADERS,
    )
    assert response.status_code == 404


def test_escalate_signoff_unknown_agenda_is_404(client):
    _seed_signoff_ready(client)
    response = client.post(
        "/api/meetings/MTG1/agenda/AG-999/escalate-signoff",
        json={"parent_meeting_id": "MTG2", "confirmed": True}, headers=HEADERS,
    )
    assert response.status_code == 404


def test_escalate_signoff_rejects_non_signoff_agenda(client):
    _schedule(client)
    client.post("/api/meetings", json={"meeting_id": "MTG2", "title": "P",
                                       "date": "2026-10-15", "confirmed": True},
                headers=HEADERS)
    _add(client, "agenda", {"title": "Regular agenda item"})
    response = client.post(
        "/api/meetings/MTG1/agenda/AG-001/escalate-signoff",
        json={"parent_meeting_id": "MTG2", "confirmed": True}, headers=HEADERS,
    )
    assert response.status_code == 400


def test_escalate_signoff_unknown_parent_is_404(client):
    agenda_id = _seed_signoff_ready(client)
    response = client.post(
        f"/api/meetings/MTG1/agenda/{agenda_id}/escalate-signoff",
        json={"parent_meeting_id": "NOPE", "confirmed": True}, headers=HEADERS,
    )
    assert response.status_code == 404


def test_escalate_signoff_rejects_completed_parent(client):
    agenda_id = _seed_signoff_ready(client)
    client.post(
        "/api/meetings/MTG2/field",
        json={"field": "status", "value": "Completed", "confirmed": True},
        headers=HEADERS,
    )
    response = client.post(
        f"/api/meetings/MTG1/agenda/{agenda_id}/escalate-signoff",
        json={"parent_meeting_id": "MTG2", "confirmed": True}, headers=HEADERS,
    )
    assert response.status_code == 400
    assert "Scheduled" in response.get_json()["error"]


def test_escalate_signoff_rejects_self(client):
    agenda_id = _seed_signoff_ready(client)
    response = client.post(
        f"/api/meetings/MTG1/agenda/{agenda_id}/escalate-signoff",
        json={"parent_meeting_id": "MTG1", "confirmed": True}, headers=HEADERS,
    )
    assert response.status_code == 400
    assert "itself" in response.get_json()["error"]
