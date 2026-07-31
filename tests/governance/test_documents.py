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
