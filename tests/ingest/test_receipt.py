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
"""Ingest-receipt aggregate: pure fold/rules and DB-backed command + projection."""
from __future__ import annotations

from src.ingest.receipt import (
    get_receipt,
    list_receipts,
    receipt_id,
    rebuild_receipts_view,
    record_receipt,
)
from src.ingest.receipt._rules import decide_record
from src.ingest.receipt._state import EVENT_INGESTED, apply, initial_state

PROV = {"source_repo": "TestRepo", "commit": "abc", "producer": "p",
        "producer_version": "1", "generated_at": "2026-07-15T00:00:00Z"}


def test_receipt_id_format():
    assert receipt_id("data-lineage", "TestRepo") == "data-lineage:TestRepo"


def test_apply_ingested_sets_state():
    _, payload = decide_record(
        initial_state(), artifact="data-lineage", source_repo="TestRepo",
        content_hash="h", provenance=PROV, summary={"run_count": 1},
    )
    state = apply(initial_state(), EVENT_INGESTED, payload)
    assert state.exists and state.artifact == "data-lineage"
    assert state.summary == {"run_count": 1}


def test_apply_ignores_unknown_event():
    assert apply(initial_state(), "Nope", {}) == initial_state()


def test_record_receipt_projects():
    record_receipt(
        artifact="data-lineage", source_repo="TestRepo", content_hash="h",
        provenance=PROV, summary={"run_count": 2}, actor="ingest:TestRepo",
    )
    rebuild_receipts_view()
    receipt = get_receipt("data-lineage", "TestRepo")
    assert receipt["artifact"] == "data-lineage"
    assert receipt["data"]["summary"] == {"run_count": 2}
    assert len(list_receipts()) == 1


def test_second_receipt_supersedes_first():
    # Two receipts on the same (artifact, repo) stream: the fold in _load must
    # replay the prior event, and the latest content hash wins.
    record_receipt(
        artifact="data-lineage", source_repo="TestRepo", content_hash="h1",
        provenance=PROV, summary={"run_count": 1}, actor="ingest:TestRepo",
    )
    record_receipt(
        artifact="data-lineage", source_repo="TestRepo", content_hash="h2",
        provenance=PROV, summary={"run_count": 2}, actor="ingest:TestRepo",
    )
    rebuild_receipts_view()
    receipt = get_receipt("data-lineage", "TestRepo")
    assert receipt["content_hash"] == "h2"
    assert receipt["version"] == 2


def test_get_receipt_absent_returns_none():
    assert get_receipt("data-lineage", "NoSuchRepo") is None
