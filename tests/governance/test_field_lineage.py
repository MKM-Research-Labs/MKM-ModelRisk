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
"""Field-lineage aggregate: pure fold/rules and DB-backed command + projection.

The registry maps every field on every report to where its value comes from
(BCBS 239 Principle 3), so the derived counts are per report and per field.
"""
from __future__ import annotations

import pytest

from src.governance.errors import DomainError
from src.governance.field_lineage import (
    get_registry,
    ingest_field_lineage,
    list_registries,
    rebuild_field_lineage_view,
)
from src.governance.field_lineage._rules import decide_ingest, field_count
from src.governance.field_lineage._state import EVENT_INGESTED, apply, initial_state
from src.ingest._envelope import content_hash

PROV = {
    "source_repo": "TestRepo", "commit": "abc123", "producer": "lineage.field_usage",
    "producer_version": "1.0.0", "generated_at": "2026-07-21T00:00:00Z",
}


def _registry(fields=("total_pnl",)):
    return {
        "version": "1.0.0",
        "reports": {"eod_report": {"label": "End of Day", "sections": {
            "summary": {"label": "Summary", "fields": {
                f: {"source_file": "blotter.json", "source_field": f} for f in fields}}}}},
    }


# --- pure ---

def test_apply_ingested_sets_state():
    payload = {"registry": _registry(), "content_hash": "h", "provenance": PROV}
    state = apply(initial_state(), EVENT_INGESTED, payload)
    assert state.exists and state.content_hash == "h"


def test_apply_ignores_unknown_event():
    assert apply(initial_state(), "Whatever", {}) == initial_state()


def test_field_count_totals_across_reports_and_sections():
    assert field_count(_registry(("a", "b", "c"))) == 3
    assert field_count({}) == 0  # nothing catalogued yet


def test_decide_ingest_builds_counts():
    event_type, payload = decide_ingest(
        initial_state(), registry=_registry(("a", "b")), provenance=PROV, content_hash="h"
    )
    assert event_type == EVENT_INGESTED
    assert payload["report_count"] == 1 and payload["field_count"] == 2


def test_decide_ingest_rejects_non_dict():
    with pytest.raises(DomainError):
        decide_ingest(initial_state(), registry=[], provenance=PROV, content_hash="h")


# --- DB-backed ---

def _ingest(registry):
    return ingest_field_lineage(
        source_repo="TestRepo", registry=registry, provenance=PROV,
        content_hash=content_hash(registry), actor="ingest:TestRepo",
    )


def test_ingest_new_registry_appends_and_projects():
    assert _ingest(_registry()) is not None
    rebuild_field_lineage_view()
    doc = get_registry("TestRepo")
    assert doc["content_hash"] == content_hash(_registry())
    assert doc["data"]["report_count"] == 1 and doc["data"]["field_count"] == 1


def test_ingest_identical_registry_is_idempotent():
    _ingest(_registry())
    assert _ingest(_registry()) is None  # same content hash -> no new event


def test_ingest_changed_registry_appends_new_version():
    first = _ingest(_registry(("a",)))
    second = _ingest(_registry(("a", "b")))
    assert first is not None and second is not None
    rebuild_field_lineage_view()
    assert get_registry("TestRepo")["data"]["field_count"] == 2
    assert len(list_registries()) == 1


def test_get_registry_absent_returns_none():
    assert get_registry("NoSuchRepo") is None


def test_rebuild_ignores_other_aggregates():
    """The log is shared, so the rebuild must skip events of every other type."""
    from src.governance.data_lineage import ingest_data_lineage

    manifest = {"runs": {"r1": ["s1"]},
                "steps": {"s1": {"run_id": "r1", "generator": "g", "status": "success",
                                 "inputs": {}, "outputs": {}}}}
    ingest_data_lineage(source_repo="TestRepo", manifest=manifest, provenance=PROV,
                        content_hash=content_hash(manifest), actor="ingest:TestRepo")
    _ingest(_registry())
    assert rebuild_field_lineage_view() == 1  # the data-lineage event is not counted
