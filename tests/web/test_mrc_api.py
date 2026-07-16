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
    # mrc is the anchor; chair is derived (from the MRC), not a meeting field.
    assert "mrc" in field_keys and "location" in field_keys
    assert "chair" not in field_keys
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


def test_models_in_scope_surfaces_analysis_outcome_and_note(client):
    # Regression: the /models view feeds the Analysis panel's Outcome dropdown and
    # Discussion note. If the endpoint drops these item fields, a saved outcome
    # re-renders as "Pending" and the note re-renders blank ("does not stick").
    client.post(
        "/api/models",
        json={"model_id": "MKM-Y", "name": "Example Y", "confirmed": True,
              "fields": {"tier": 1, "rag_rating": "Amber"}},
        headers=HEADERS,
    )
    _schedule(client)
    _add(client, "models_in_scope",
         {"model_id": "MKM-Y", "analysis_status": "Reviewed — agreed to proceed",
          "analysis_note": "Agreed to proceed with caveats"})
    rows = client.get("/api/meetings/MTG1/models").get_json()
    assert rows[0]["analysis_status"] == "Reviewed — agreed to proceed"
    assert rows[0]["analysis_note"] == "Agreed to proceed with caveats"


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
        json={"field": "location", "value": "Boardroom 2", "confirmed": True}, headers=HEADERS,
    )
    assert response.get_json()["data"]["location"] == "Boardroom 2"


def test_update_removed_meeting_field_is_400(client):
    """chair / company / division / department are no longer editable — they're
    derived from the meeting's MRC binding on read."""
    _schedule(client)
    response = client.post(
        "/api/meetings/MTG1/field",
        json={"field": "chair", "value": "Dr Patel", "confirmed": True}, headers=HEADERS,
    )
    assert response.status_code == 400


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


def test_add_applies_without_confirmation(client):
    # Adding a non-critical agenda item is not gated by confirm-to-amend.
    _schedule(client)
    response = client.post(
        "/api/meetings/MTG1/collections/agenda",
        json={"fields": {"title": "x"}}, headers=HEADERS,
    )
    assert response.status_code == 201
    assert "x" in [a["title"] for a in response.get_json()["data"]["agenda"]]


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


def test_bulk_add_applies_without_confirmation(client):
    # Bulk-adding non-critical items is not gated by confirm-to-amend.
    _schedule(client)
    response = client.post(
        "/api/meetings/MTG1/collections/minutes/bulk",
        json={"items": [{"fields": {"title": "x"}}]},
        headers=HEADERS,
    )
    assert response.status_code == 201
    assert response.get_json()["data"]["minutes"][0]["title"] == "x"


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


def test_set_models_in_scope_applies_without_confirmation(client):
    # Setting the in-scope models is not gated by confirm-to-amend.
    _schedule(client)
    response = client.post(
        "/api/meetings/MTG1/collections/models_in_scope/set",
        json={"model_ids": ["M-A"]}, headers=HEADERS,
    )
    assert response.status_code == 200
    scope = response.get_json()["data"].get("models_in_scope") or []
    assert [m["model_id"] for m in scope] == ["M-A"]

