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
"""Tests for the MRC-meeting HTTP API (fields, scheduling, collections)."""
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


def test_field_specs_endpoint(client):
    specs = client.get("/api/meetings/fields").get_json()
    field_keys = [f["key"] for f in specs["fields"]]
    assert "chair" in field_keys and "location" in field_keys
    collection_keys = [c["key"] for c in specs["collections"]]
    assert "agenda" in collection_keys and "participants" in collection_keys


def test_schedule_get_and_list(client):
    assert _schedule(client).status_code == 201
    assert [m["meeting_id"] for m in client.get("/api/meetings").get_json()] == ["MTG1"]
    assert client.get("/api/meetings/MTG1").get_json()["status"] == "Scheduled"


def test_get_unknown_meeting_is_404(client):
    assert client.get("/api/meetings/none").status_code == 404


def test_models_in_scope_joins_inventory(client):
    client.post(
        "/api/models",
        json={"model_id": "MKM-X", "name": "Example X", "confirmed": True,
              "fields": {"tier": 2, "rag_rating": "Green", "next_review_date": "2020-01-01"}},
        headers=HEADERS,
    )
    _schedule(client)
    _add(client, "models_in_scope", {"model_id": "MKM-X"})
    rows = client.get("/api/meetings/MTG1/models").get_json()
    assert rows[0]["model_id"] == "MKM-X"
    assert rows[0]["name"] == "Example X"
    assert rows[0]["tier"] == 2
    assert rows[0]["rag_rating"] == "Green"
    assert rows[0]["review_status"] == "Overdue"


def test_models_in_scope_handles_unknown_model(client):
    _schedule(client)
    _add(client, "models_in_scope", {"model_id": "GHOST"})
    rows = client.get("/api/meetings/MTG1/models").get_json()
    assert rows[0]["model_id"] == "GHOST"
    assert rows[0]["name"] is None
    assert rows[0]["review_status"] == "Not Scheduled"


def test_models_endpoint_unknown_meeting_is_404(client):
    assert client.get("/api/meetings/none/models").status_code == 404


def test_pack_pdf_endpoint(client, monkeypatch):
    monkeypatch.setattr("src.governance.mrc.pack.compile_tex", lambda tex, assets=None: b"%PDF-stub")
    _schedule(client)
    response = client.get("/api/meetings/MTG1/pack.pdf")
    assert response.status_code == 200
    assert response.mimetype == "application/pdf"
    assert response.data.startswith(b"%PDF")


def test_pack_pdf_unknown_meeting_is_404(client):
    assert client.get("/api/meetings/none/pack.pdf").status_code == 404


def test_update_meeting_field(client):
    _schedule(client)
    response = client.post(
        "/api/meetings/MTG1/field",
        json={"field": "chair", "value": "Dr Patel", "confirmed": True}, headers=HEADERS,
    )
    assert response.get_json()["data"]["chair"] == "Dr Patel"


def test_collection_add_update_remove(client):
    _schedule(client)
    added = _add(client, "actions", {"description": "Follow up", "owner": "bob"})
    assert added.status_code == 201
    assert added.get_json()["data"]["actions"][0]["item_id"] == "A-001"

    updated = client.post(
        "/api/meetings/MTG1/collections/actions/A-001",
        json={"fields": {"status": "Closed"}, "confirmed": True}, headers=HEADERS,
    )
    assert updated.get_json()["data"]["actions"][0]["status"] == "Closed"

    removed = client.post(
        "/api/meetings/MTG1/collections/actions/A-001/delete",
        json={"confirmed": True}, headers=HEADERS,
    )
    assert removed.get_json()["data"]["actions"] == []


def test_add_missing_required_is_400(client):
    _schedule(client)
    assert _add(client, "agenda", {"presenter": "Alice"}).status_code == 400


def test_invalid_meeting_status_is_400(client):
    _schedule(client)
    response = client.post(
        "/api/meetings/MTG1/field",
        json={"field": "status", "value": "Bogus", "confirmed": True}, headers=HEADERS,
    )
    assert response.status_code == 400


def test_add_without_confirmation_is_409(client):
    _schedule(client)
    response = client.post(
        "/api/meetings/MTG1/collections/agenda",
        json={"fields": {"title": "x"}}, headers=HEADERS,
    )
    assert response.status_code == 409


def test_bulk_add_collection_items(client):
    """Three populated rows and two blank ones produce three events."""
    _schedule(client)
    response = client.post(
        "/api/meetings/MTG1/collections/minutes/bulk",
        json={
            "items": [
                {"fields": {"title": "Welcome", "presenter": "Chair"}},
                {"fields": {"title": "Approvals", "text": "Two approved."}},
                {"fields": {}},
                {"fields": {"title": "AOB"}},
                {"fields": {"title": "  ", "text": ""}},  # whitespace-only, skipped
            ],
            "confirmed": True,
        },
        headers=HEADERS,
    )
    assert response.status_code == 201
    minutes = response.get_json()["data"]["minutes"]
    assert [m["title"] for m in minutes] == ["Welcome", "Approvals", "AOB"]


def test_bulk_add_without_confirmation_is_409(client):
    _schedule(client)
    response = client.post(
        "/api/meetings/MTG1/collections/minutes/bulk",
        json={"items": [{"fields": {"title": "x"}}]},
        headers=HEADERS,
    )
    assert response.status_code == 409


def _set_scope(client, model_ids):
    return client.post(
        "/api/meetings/MTG1/collections/models_in_scope/set",
        json={"model_ids": model_ids, "confirmed": True}, headers=HEADERS,
    )


def test_set_models_in_scope_adds_and_removes(client):
    """The /set endpoint diffs the desired set against the current state."""
    _schedule(client)
    _add(client, "models_in_scope", {"model_id": "M-A"})
    _add(client, "models_in_scope", {"model_id": "M-B"})

    # Desired: keep B, drop A, add C.
    response = _set_scope(client, ["M-B", "M-C"])
    assert response.status_code == 200
    scope = response.get_json()["data"]["models_in_scope"]
    assert {item["model_id"] for item in scope} == {"M-B", "M-C"}


def test_set_models_in_scope_no_change_is_noop(client):
    _schedule(client)
    _add(client, "models_in_scope", {"model_id": "M-A"})
    response = _set_scope(client, ["M-A"])
    assert response.status_code == 200
    scope = response.get_json()["data"]["models_in_scope"]
    assert [item["model_id"] for item in scope] == ["M-A"]


def test_set_models_in_scope_unknown_meeting_is_404(client):
    response = client.post(
        "/api/meetings/NOPE/collections/models_in_scope/set",
        json={"model_ids": ["M-A"], "confirmed": True}, headers=HEADERS,
    )
    assert response.status_code == 404


def test_set_models_in_scope_without_confirmation_is_409(client):
    _schedule(client)
    response = client.post(
        "/api/meetings/MTG1/collections/models_in_scope/set",
        json={"model_ids": ["M-A"]}, headers=HEADERS,
    )
    assert response.status_code == 409


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
