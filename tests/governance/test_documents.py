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
"""Tests for the generic document-attachment store."""
from __future__ import annotations

import pytest

from src.governance.documents import add_document, find_document, list_documents, remove_document
from src.governance.errors import DomainError

AGG = "ModelInventoryEntry"


def _add(item="report.pdf", category="Analysis"):
    return add_document(
        aggregate_type=AGG, aggregate_id="M1", scope="model/M1", category=category,
        filename=item, data=b"data", description="A report", actor="user",
    )


def test_add_and_list():
    _add()
    docs = list_documents(AGG, "M1")
    assert docs[0]["item_id"] == "DOC-001"
    assert docs[0]["category"] == "Analysis"
    assert docs[0]["original_name"] == "report.pdf"
    assert docs[0]["size"] == 4


def test_find_and_remove():
    _add()
    assert find_document(AGG, "M1", "DOC-001") is not None
    remove_document(aggregate_type=AGG, aggregate_id="M1", item_id="DOC-001", actor="user")
    assert list_documents(AGG, "M1") == []
    assert find_document(AGG, "M1", "DOC-001") is None


def test_remove_unknown_raises():
    with pytest.raises(DomainError):
        remove_document(aggregate_type=AGG, aggregate_id="M1", item_id="DOC-999", actor="user")
