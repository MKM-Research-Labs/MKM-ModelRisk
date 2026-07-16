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
"""Targeted coverage: audit change-diffs, ToR upload edge cases, small endpoints."""
from __future__ import annotations

import io

from src.files import upload_path
from tests.web.conftest import HEADERS


def _register_model(client, model_id="M1"):
    return client.post(
        "/api/models",
        json={"model_id": model_id, "name": "M", "confirmed": True,
              "fields": {"rag_rating": "Amber"}}, headers=HEADERS,
    )


def test_audit_diffs_added_updated_and_removed_collection_items(client):
    """The audit feed computes a field-level change diff for add / update / remove."""
    _register_model(client)
    add = client.post("/api/models/M1/collections/limitations",
                      json={"fields": {"description": "Edge case", "impact": "Low"}},
                      headers=HEADERS)
    assert add.status_code == 201
    item_id = add.get_json()["data"]["limitations"][0]["item_id"]
    client.post(f"/api/models/M1/collections/limitations/{item_id}",
                json={"fields": {"impact": "High"}, "confirmed": True}, headers=HEADERS)
    client.post(f"/api/models/M1/collections/limitations/{item_id}/delete",
                json={"confirmed": True}, headers=HEADERS)

    audit = client.get("/api/audit").get_json()
    assert audit
    # An add diffs every field from None; an update reports from/to; a remove
    # diffs every field to None. At least one entry carries a computed change.
    assert any(e.get("changes") for e in audit)
    removed = [e for e in audit if any(c["to"] is None for c in e.get("changes") or [])]
    assert removed


def test_approve_signoff_files_minute_with_chair_as_presenter(client):
    """When the committee has a chair, the sign-off minute is filed under them."""
    from tests.web import test_mrc_signoff_api as ms
    client.post(
        "/api/reference/collections/mrc",
        json={"fields": {"value": "MRC-CO", "name": "Committee", "level": "Company",
                         "chair": "Cara Chair", "quorum_require_chair": "No",
                         "quorum_require_secretary": "No", "quorum_min_voting": "0"},
              "confirmed": True}, headers=HEADERS)
    ms._register_subject_model(client, tier=1, materiality="Low", complexity="Low")
    ms._schedule_meeting(client)
    ms._request_signoff(client)
    agenda_id = ms._signoff_item(client)["item_id"]
    resp = client.post(f"/api/meetings/MTG1/agenda/{agenda_id}/approve-signoff",
                       json={"confirmed": True}, headers=HEADERS)
    assert resp.status_code == 200
    minutes = resp.get_json()["meeting"]["data"].get("minutes") or []
    filed = [m for m in minutes if "Sign-off approved" in (m.get("title") or "")]
    assert filed and filed[0]["presenter"] == "Cara Chair"


def test_static_assets_are_not_cached(client):
    resp = client.get("/static/js/api.js")
    assert "no-store" in resp.headers.get("Cache-Control", "")


def test_product_actions_unknown_is_404(client):
    assert client.get("/api/products/NOPE/actions").status_code == 404


# --- MRC committee Terms-of-Reference upload/download edge cases ------------

def _seed_committee(client, **extra):
    """Create a committee and return its generated item_id (the POST echoes the
    updated ``mrc`` list; the plain GET /api/reference does not key by list)."""
    res = client.post(
        "/api/reference/collections/mrc",
        json={"fields": {"value": "MRC-CO", "name": "Committee", "level": "Company", **extra},
              "confirmed": True}, headers=HEADERS)
    return res.get_json()["mrc"][0]["item_id"]


def test_mrc_tor_upload_requires_a_file(client):
    item_id = _seed_committee(client)
    resp = client.post(f"/api/reference/collections/mrc/{item_id}/tor",
                       data={}, content_type="multipart/form-data", headers=HEADERS)
    assert resp.status_code == 400
    assert "no file" in resp.get_json()["error"]


def test_mrc_tor_upload_rejects_disallowed_type(client):
    item_id = _seed_committee(client)
    resp = client.post(f"/api/reference/collections/mrc/{item_id}/tor",
                       data={"file": (io.BytesIO(b"x"), "tor.exe")},
                       content_type="multipart/form-data", headers=HEADERS)
    assert resp.status_code == 400


def test_mrc_tor_download_when_file_is_gone_is_404(client):
    item_id = _seed_committee(client)
    up = client.post(f"/api/reference/collections/mrc/{item_id}/tor",
                     data={"file": (io.BytesIO(b"%PDF"), "tor.pdf")},
                     content_type="multipart/form-data", headers=HEADERS)
    assert up.status_code == 201
    item = next(i for i in up.get_json()["mrc"] if i["item_id"] == item_id)
    upload_path("mrc", item["tor_filename"]).unlink()
    assert client.get(f"/api/reference/collections/mrc/{item_id}/tor").status_code == 404


def test_mrc_resolution_matches_department_then_division(client):
    """matching_mrc prefers a Department-level committee, then Division-level."""
    client.post("/api/reference/collections/mrc",
                json={"fields": {"value": "MRC-DEPT", "name": "Dept", "level": "Department",
                                 "scope_value": "Rates"}, "confirmed": True}, headers=HEADERS)
    client.post("/api/reference/collections/mrc",
                json={"fields": {"value": "MRC-DIV", "name": "Div", "level": "Division",
                                 "scope_value": "Markets"}, "confirmed": True}, headers=HEADERS)
    # A model in Markets/Rates resolves to the Department committee.
    client.post("/api/models",
                json={"model_id": "MD", "name": "Dept model", "confirmed": True,
                      "fields": {"division": "Markets", "department": "Rates"}}, headers=HEADERS)
    dept = client.get("/api/models/MD/mrc").get_json()
    assert dept["mrc"]["value"] == "MRC-DEPT" and dept["level"] == "Department"
    # A model in Markets with no matching department falls back to Division.
    client.post("/api/models",
                json={"model_id": "MV", "name": "Div model", "confirmed": True,
                      "fields": {"division": "Markets", "department": "Unmatched"}}, headers=HEADERS)
    div = client.get("/api/models/MV/mrc").get_json()
    assert div["mrc"]["value"] == "MRC-DIV" and div["level"] == "Division"
