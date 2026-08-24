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
"""The governance-documents id repair, as it will be run against the estate.

Two live documents on the top-level Documents area share DOC-017 there, because
ids were once numbered from the item count. The script re-files each under its
own id; this exercises it end to end on the same aggregate the real run touches.
"""
from __future__ import annotations

from scripts.repair_duplicate_document_ids import AGGREGATE, AGGREGATE_ID, repair
from src.governance import collections as coll
from src.governance.documents import add_document, list_documents, remove_document


def _upload(name, description=""):
    return add_document(aggregate_type=AGGREGATE, aggregate_id=AGGREGATE_ID,
                        scope="governance", filename=name, data=b"%PDF-",
                        description=description, actor="a")


def _collide(monkeypatch, name):
    """Upload under the old count-based numbering, which reissues a live id."""
    monkeypatch.setattr(coll, "next_item_id",
                        lambda items, prefix: f"{prefix}-{len(items) + 1:03d}")
    doc = _upload(name)
    monkeypatch.undo()
    return doc


def test_repair_separates_two_documents_that_share_an_id(monkeypatch):
    gone = _upload("gone.pdf")
    kept = _upload("SR2602.pdf", description="Supervisory statement")
    remove_document(aggregate_type=AGGREGATE, aggregate_id=AGGREGATE_ID,
                    item_id=gone["item_id"], actor="a")
    clash = _collide(monkeypatch, "space-economy.pdf")
    assert clash["item_id"] == kept["item_id"]

    moved = repair()
    docs = list_documents(AGGREGATE, AGGREGATE_ID)
    assert len(moved) == 2
    assert len({d["item_id"] for d in docs}) == len(docs) == 2
    assert {d["original_name"] for d in docs} == {"SR2602.pdf", "space-economy.pdf"}
    kept_after = next(d for d in docs if d["original_name"] == "SR2602.pdf")
    assert kept_after["description"] == "Supervisory statement"
    assert kept_after["filename"] == kept["filename"], "the stored file is untouched"


def test_repair_is_safe_to_re_run(monkeypatch):
    _upload("a.pdf")
    assert repair() == []
