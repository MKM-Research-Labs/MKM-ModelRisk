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
"""Feature B: the Audit tab is the complete record. Every kind of mutation the
UI can make against a model — a scalar field edit, a collection entry, and a
document upload — must surface on the audit trail with its before/after change."""
from __future__ import annotations

import io

from tests.web.conftest import HEADERS


def _events_for(client, model_id):
    return [e for e in client.get("/api/audit").get_json()
            if e["aggregate_id"] == model_id]


def test_field_edit_collection_add_and_upload_all_appear_on_audit(client):
    client.post("/api/models", json={"model_id": "M1", "name": "Alpha", "confirmed": True},
                headers=HEADERS)

    # 1. a scalar field edit — recorded with its before/after change.
    client.post("/api/models/M1/field",
                json={"field": "owner", "value": "bob", "confirmed": True, "reason": "assigned"},
                headers=HEADERS)
    # 2. a collection entry.
    client.post("/api/models/M1/collections/limitations",
                json={"fields": {"description": "Extrapolation risk"}, "confirmed": True},
                headers=HEADERS)
    # 3. a document upload.
    client.post("/api/models/M1/documents",
                data={"file": (io.BytesIO(b"PDFDATA"), "report.pdf"),
                      "category": "Test Results", "description": "Q1"},
                content_type="multipart/form-data", headers=HEADERS)

    events = _events_for(client, "M1")
    by_type = {e["event_type"] for e in events}
    assert "ModelFieldUpdated" in by_type
    assert "CollectionItemAdded" in by_type

    # The field edit carries the before/after so the tab can render old -> new.
    field_edit = next(e for e in events if e["event_type"] == "ModelFieldUpdated"
                      and any(c["field"] == "owner" for c in e["changes"]))
    change = next(c for c in field_edit["changes"] if c["field"] == "owner")
    assert change["to"] == "bob"

    # Both the limitation entry and the document upload are collection adds; the
    # upload records the stored file so the tab shows what was attached.
    adds = [e for e in events if e["event_type"] == "CollectionItemAdded"]
    collections_touched = {e["target"]["collection"] for e in adds if e.get("target")}
    assert "limitations" in collections_touched
    assert "documents" in collections_touched
    upload = next(e for e in adds if e["target"]["collection"] == "documents")
    assert any((c["field"], c["to"]) == ("original_name", "report.pdf") for c in upload["changes"])
