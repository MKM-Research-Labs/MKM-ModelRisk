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
"""Amending a stored document's metadata."""
from __future__ import annotations

import pytest

from src.governance.documents import (add_document, list_documents, model_scope,
                                      reissue_duplicate_ids, remove_document,
                                      update_document)
from src.governance.errors import DomainError

AGG = "ModelInventoryEntry"


def _add(category="Analysis", name="a.pdf"):
    return add_document(aggregate_type=AGG, aggregate_id="M1", scope=model_scope("M1"),
                        filename=name, data=b"%PDF-", description="d",
                        actor="a", category=category)


def test_recategorising_keeps_the_file_and_the_item_id():
    """Recategorising is a metadata change, not a re-upload: remove-and-add would
    reissue ids and silently break every reference to the document."""
    doc = _add()
    update_document(aggregate_type=AGG, aggregate_id="M1", item_id=doc["item_id"],
                    fields={"category": "Sensitivity"}, actor="a")
    after = list_documents(AGG, "M1")
    assert len(after) == 1, "amending must not add a second record"
    assert after[0]["item_id"] == doc["item_id"]
    assert after[0]["category"] == "Sensitivity"
    assert after[0]["filename"] == doc["filename"], "the stored file is untouched"


def test_amending_an_unknown_document_is_refused():
    _add()
    with pytest.raises(DomainError, match="unknown document"):
        update_document(aggregate_type=AGG, aggregate_id="M1", item_id="DOC-999",
                        fields={"category": "Sensitivity"}, actor="a")


def test_clean_model_types_trims_dedupes_and_keeps_order():
    from src.governance.documents import clean_model_types
    assert clean_model_types(None) == []
    assert clean_model_types([]) == []
    assert clean_model_types([" Hazard ", "Pricing", "Hazard", ""]) == ["Hazard", "Pricing"]


def test_external_document_carries_model_types_but_no_category():
    from src.governance.documents import GOVERNANCE_DOCUMENTS_AGGREGATE as GDA
    doc = add_document(
        aggregate_type=GDA, aggregate_id="global", scope="governance",
        filename="ref.pdf", data=b"%PDF-", description="", actor="a",
        model_types=["Hazard", "Regulatory", "Hazard"])
    assert doc["model_types"] == ["Hazard", "Regulatory"]
    assert doc["category"] == ""


def test_model_types_default_to_empty_list():
    doc = _add(name="notypes.pdf")
    assert doc["model_types"] == []


def test_scope_helpers_name_the_upload_directories():
    from src.governance.documents import client_scope, model_scope
    assert model_scope("MKM-DD-001") == "model/MKM-DD-001"
    assert client_scope("CL-01") == "client/CL-01"


def _add_with_count_numbering(monkeypatch, name):
    """Upload the way ids used to be minted — from the item count, not the highest
    in use — which is how two live documents came to share one id."""
    from src.governance import collections as coll
    monkeypatch.setattr(coll, "next_item_id",
                        lambda items, prefix: f"{prefix}-{len(items) + 1:03d}")
    doc = _add(name=name)
    monkeypatch.undo()
    return doc


def test_a_removed_documents_id_is_not_handed_to_the_next_upload():
    first, second = _add(name="a.pdf"), _add(name="b.pdf")
    remove_document(aggregate_type=AGG, aggregate_id="M1", item_id=first["item_id"], actor="a")
    third = _add(name="c.pdf")
    assert third["item_id"] != second["item_id"], "an id in use must never be reissued"


def test_documents_sharing_an_id_are_reissued_one_each(monkeypatch):
    # Remove an early document and the count points back at a live id: one left,
    # so the next upload is numbered 002 — which DOC-002 already holds.
    doomed = _add(name="gone.pdf")                     # DOC-001
    kept = _add(name="keep.pdf")                       # DOC-002
    remove_document(aggregate_type=AGG, aggregate_id="M1", item_id=doomed["item_id"], actor="a")
    clash = _add_with_count_numbering(monkeypatch, "clash.pdf")
    assert clash["item_id"] == kept["item_id"], "the state this repair exists for"

    moved = reissue_duplicate_ids(aggregate_type=AGG, aggregate_id="M1", actor="fix")
    after = list_documents(AGG, "M1")
    assert len(after) == 2, "a repair must not add or lose a document"
    assert len({d["item_id"] for d in after}) == 2
    assert {m["name"] for m in moved} == {"keep.pdf", "clash.pdf"}
    assert all(m["was"] == kept["item_id"] for m in moved)

    # Everything but the id survives, so the file still downloads and the row still
    # reads the same.
    by_name = {d["original_name"]: d for d in after}
    assert by_name["keep.pdf"]["filename"] == kept["filename"]
    assert by_name["keep.pdf"]["uploaded_at"] == kept["uploaded_at"]
    assert by_name["clash.pdf"]["description"] == "d"


def test_reissuing_is_idempotent_when_every_id_is_already_unique():
    _add(name="a.pdf")
    assert reissue_duplicate_ids(aggregate_type=AGG, aggregate_id="M1", actor="fix") == []
