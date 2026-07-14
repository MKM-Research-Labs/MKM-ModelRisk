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


def _seed_mrc(client, value="MRC-CO", level="Company", scope_value=None):
    """A Company-level MRC covering every model. Quorum is switched off so its
    meetings are quorate without an attended roster — these tests exercise
    sign-off mechanics; the quorum gate is covered in test_mrc_quorum.py."""
    fields = {"value": value, "name": value, "level": level,
              "quorum_require_chair": "No", "quorum_require_secretary": "No",
              "quorum_min_voting": "0"}
    if scope_value:
        fields["scope_value"] = scope_value
    return client.post(
        "/api/reference/collections/mrc",
        json={"fields": fields, "confirmed": True}, headers=HEADERS,
    )


def _schedule(client, meeting_id="MTG1", mrc="MRC-CO", date="2026-06-30"):
    return client.post(
        "/api/meetings",
        json={"meeting_id": meeting_id, "title": "Q2 MRC", "date": date,
              "fields": {"mrc": mrc}, "confirmed": True},
        headers=HEADERS,
    )


def _add(client, collection, fields):
    return client.post(
        "/api/meetings/MTG1/collections/" + collection,
        json={"fields": fields, "confirmed": True}, headers=HEADERS,
    )


def _schedule_meeting(client, meeting_id="MTG1", mrc="MRC-CO", date="2026-09-15"):
    return client.post(
        "/api/meetings",
        json={"meeting_id": meeting_id, "title": "Q3", "date": date,
              "fields": {"mrc": mrc}, "confirmed": True},
        headers=HEADERS,
    )


def _register_subject_model(client, model_id="M1", **fields):
    return client.post(
        "/api/models",
        json={"model_id": model_id, "name": "Subject",
              "fields": {"rag_rating": "Amber", **fields}, "confirmed": True},
        headers=HEADERS,
    )


def _request_signoff(client, model_id="M1", proposed_rag="Green"):
    return client.post(
        f"/api/models/{model_id}/request-signoff",
        json={"proposed_rag": proposed_rag, "confirmed": True},
        headers=HEADERS,
    )


def _signoff_agenda_items(agenda):
    """The sign-off items on a meeting's agenda — every meeting also seeds the
    five standing agenda items, so a sign-off is never alone or necessarily first."""
    return [a for a in agenda if a.get("subject_model_id") or a.get("subject_product_id")]


def _signoff_item(client, meeting_id="MTG1"):
    agenda = client.get(f"/api/meetings/{meeting_id}").get_json()["data"]["agenda"]
    return _signoff_agenda_items(agenda)[0]


def test_request_signoff_attaches_to_scheduled_meeting_of_matching_mrc(client):
    _seed_mrc(client)
    _register_subject_model(client)
    _schedule_meeting(client)
    response = _request_signoff(client)
    assert response.status_code == 201
    agenda = client.get("/api/meetings/MTG1").get_json()["data"]["agenda"]
    items = _signoff_agenda_items(agenda)
    assert len(items) == 1
    assert items[0]["subject_model_id"] == "M1"
    assert items[0]["proposed_rag"] == "Green"
    assert items[0]["status"] == "Pending"
    # The model-side request is now Attached to that meeting.
    req = response.get_json()["data"]["rag_signoff_requests"][0]
    assert req["status"] == "Attached" and req["meeting_id"] == "MTG1"


def test_request_signoff_without_meeting_queues_pending(client):
    _seed_mrc(client)
    _register_subject_model(client)
    response = _request_signoff(client)
    assert response.status_code == 201
    reqs = response.get_json()["data"]["rag_signoff_requests"]
    assert len(reqs) == 1
    assert reqs[0]["status"] == "Pending" and reqs[0]["target_mrc"] == "MRC-CO"


def test_pending_request_drains_onto_newly_scheduled_meeting(client):
    _seed_mrc(client)
    _register_subject_model(client)
    _request_signoff(client)          # queued — no meeting yet
    _schedule_meeting(client)          # scheduling drains the queue onto the agenda
    agenda = client.get("/api/meetings/MTG1").get_json()["data"]["agenda"]
    items = _signoff_agenda_items(agenda)
    assert len(items) == 1 and items[0]["subject_model_id"] == "M1"
    req = client.get("/api/models/M1").get_json()["data"]["rag_signoff_requests"][0]
    assert req["status"] == "Attached" and req["meeting_id"] == "MTG1"


def test_request_signoff_blocked_without_matching_mrc(client):
    _register_subject_model(client)   # no MRC configured at all
    response = _request_signoff(client)
    assert response.status_code == 400
    assert "MRC" in response.get_json()["error"]


def test_request_signoff_rejects_unknown_model(client):
    response = _request_signoff(client, model_id="NOPE")
    assert response.status_code == 404


def test_request_signoff_requires_proposed_rag(client):
    _seed_mrc(client)
    _register_subject_model(client)
    response = client.post(
        "/api/models/M1/request-signoff",
        json={"confirmed": True}, headers=HEADERS,
    )
    assert response.status_code == 400


def test_request_signoff_ignores_completed_meeting_and_stays_pending(client):
    _seed_mrc(client)
    _register_subject_model(client)
    _schedule_meeting(client)
    client.post(
        "/api/meetings/MTG1/field",
        json={"field": "status", "value": "Completed", "confirmed": True}, headers=HEADERS,
    )
    response = _request_signoff(client)
    assert response.status_code == 201
    # A Completed meeting is not a valid target — the request waits as Pending.
    assert response.get_json()["data"]["rag_signoff_requests"][0]["status"] == "Pending"
    agenda = client.get("/api/meetings/MTG1").get_json()["data"].get("agenda") or []
    assert not _signoff_agenda_items(agenda)   # no sign-off attached (standing items aside)


def test_approve_signoff_snaps_model_rating_and_records_history(client):
    _seed_mrc(client)
    _register_subject_model(client)  # Amber
    _schedule_meeting(client)
    _request_signoff(client)  # proposes Green
    agenda_id = _signoff_item(client)["item_id"]
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
    assert _signoff_agenda_items(payload["meeting"]["data"]["agenda"])[0]["status"] == "Completed"


def test_approve_signoff_records_confirm_reason_as_comment(client):
    # "Approve with comments": when no explicit note is sent, the confirm-dialog
    # reason is captured as the sign-off history note.
    _seed_mrc(client)
    _register_subject_model(client)
    _schedule_meeting(client)
    _request_signoff(client)
    agenda_id = _signoff_item(client)["item_id"]
    response = client.post(
        f"/api/meetings/MTG1/agenda/{agenda_id}/approve-signoff",
        json={"confirmed": True, "reason": "Chair satisfied with validation"}, headers=HEADERS,
    )
    assert response.status_code == 200
    history = response.get_json()["model"]["data"]["rag_signoff_history"]
    assert history[0]["note"] == "Chair satisfied with validation"


def test_approve_signoff_sets_next_review_from_mrc(client):
    _seed_mrc(client)
    _register_subject_model(client)
    _schedule_meeting(client)
    _request_signoff(client)
    agenda_id = _signoff_item(client)["item_id"]
    resp = client.post(
        f"/api/meetings/MTG1/agenda/{agenda_id}/approve-signoff",
        json={"confirmed": True, "next_review_date": "2027-01-31"}, headers=HEADERS,
    )
    assert resp.status_code == 200
    model = resp.get_json()["model"]["data"]
    assert model["next_review_date"] == "2027-01-31"
    assert model["rag_signoff_history"][0]["outcome"] == "Approved"
    assert model["rag_signoff_history"][0]["next_review_date"] == "2027-01-31"


def test_reject_signoff_leaves_rating_and_marks_rejected(client):
    _seed_mrc(client)
    _register_subject_model(client)          # Amber
    _schedule_meeting(client)
    _request_signoff(client)                  # proposes Green
    agenda_id = _signoff_item(client)["item_id"]
    resp = client.post(
        f"/api/meetings/MTG1/agenda/{agenda_id}/reject-signoff",
        json={"confirmed": True, "next_review_date": "2027-03-31",
              "reason": "insufficient evidence"}, headers=HEADERS,
    )
    assert resp.status_code == 200
    model = resp.get_json()["model"]["data"]
    assert model["rag_rating"] == "Amber"     # NOT promoted to the proposed Green
    assert model["next_review_date"] == "2027-03-31"
    assert model["rag_signoff_requests"][0]["status"] == "Rejected"
    assert model["rag_signoff_history"][0]["outcome"] == "Rejected"
    assert _signoff_agenda_items(resp.get_json()["meeting"]["data"]["agenda"])[0]["status"] == "Rejected"


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
    _seed_mrc(client)
    _register_subject_model(client)
    _schedule_meeting(client)
    _request_signoff(client)
    payload = client.get("/api/models/M1/risk-rating").get_json()
    assert payload["pending_signoff"]["proposed_rag"] == "Green"
    assert payload["pending_signoff"]["meeting_id"] == "MTG1"
    assert payload["pending_signoff"]["status"] == "Attached"


def test_pending_signoff_is_none_without_request(client):
    _register_subject_model(client)
    payload = client.get("/api/models/M1/risk-rating").get_json()
    assert payload["pending_signoff"] is None


# --- Phase MRC-4: escalate a sign-off to a parent MRC's meeting -------------

def _seed_signoff_ready(client, meeting_id="MTG1", parent_id="MTG2"):
    """Seed an MRC, register a subject model, schedule two meetings of that
    committee, and raise a sign-off. It attaches to the earliest meeting
    (``meeting_id``). Returns that agenda item's id."""
    _seed_mrc(client)
    _register_subject_model(client)
    _schedule(client, meeting_id, date="2026-06-30")           # earliest → attach target
    _schedule(client, parent_id, date="2026-10-15")            # later parent meeting
    _request_signoff(client, model_id="M1")
    return _signoff_item(client, meeting_id)["item_id"]


def test_escalate_signoff_copies_item_to_parent_meeting(client):
    agenda_id = _seed_signoff_ready(client)
    response = client.post(
        f"/api/meetings/MTG1/agenda/{agenda_id}/escalate-signoff",
        json={"parent_meeting_id": "MTG2", "confirmed": True}, headers=HEADERS,
    )
    assert response.status_code == 200
    payload = response.get_json()
    # Original marked Escalated.
    original = _signoff_agenda_items(payload["meeting"]["data"]["agenda"])[0]
    assert original["status"] == "Escalated"
    # Parent gained a Pending sign-off item with the same subject_model_id +
    # proposed_rag, back-pointing to the original.
    parent_signoffs = _signoff_agenda_items(payload["parent"]["data"]["agenda"])
    assert len(parent_signoffs) == 1
    new_item = parent_signoffs[0]
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
