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
