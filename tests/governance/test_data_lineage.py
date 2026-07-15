# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Data-lineage aggregate: pure fold/rules and DB-backed command + projection."""
from __future__ import annotations

import pytest

from src.governance.data_lineage import (
    get_manifest,
    ingest_data_lineage,
    list_manifests,
    rebuild_data_lineage_view,
)
from src.governance.data_lineage._rules import decide_ingest
from src.governance.data_lineage._state import (
    EVENT_INGESTED,
    apply,
    initial_state,
)
from src.governance.errors import DomainError
from src.ingest._envelope import content_hash

PROV = {
    "source_repo": "TestRepo", "commit": "abc123", "producer": "modelrisk-scan",
    "producer_version": "0.1.0", "generated_at": "2026-07-15T00:00:00Z",
}


def _manifest(steps=("s1",)):
    return {
        "runs": {"r1": list(steps)},
        "steps": {s: {"run_id": "r1", "generator": "g", "status": "success",
                      "inputs": {}, "outputs": {}} for s in steps},
    }


# --- pure ---

def test_apply_ingested_sets_state():
    payload = {"manifest": _manifest(), "content_hash": "h", "provenance": PROV}
    state = apply(initial_state(), EVENT_INGESTED, payload)
    assert state.exists and state.content_hash == "h"


def test_apply_ignores_unknown_event():
    assert apply(initial_state(), "Whatever", {}) == initial_state()


def test_decide_ingest_builds_counts():
    event_type, payload = decide_ingest(
        initial_state(), manifest=_manifest(("a", "b")), provenance=PROV, content_hash="h"
    )
    assert event_type == EVENT_INGESTED
    assert payload["run_count"] == 1 and payload["step_count"] == 2


def test_decide_ingest_rejects_non_dict():
    with pytest.raises(DomainError):
        decide_ingest(initial_state(), manifest=[], provenance=PROV, content_hash="h")


# --- DB-backed ---

def _ingest(manifest):
    chash = content_hash(manifest)
    return ingest_data_lineage(
        source_repo="TestRepo", manifest=manifest, provenance=PROV,
        content_hash=chash, actor="ingest:TestRepo",
    )


def test_ingest_new_manifest_appends_and_projects():
    event = _ingest(_manifest())
    assert event is not None
    rebuild_data_lineage_view()
    doc = get_manifest("TestRepo")
    assert doc["content_hash"] == content_hash(_manifest())
    assert doc["data"]["run_count"] == 1


def test_ingest_identical_manifest_is_idempotent():
    _ingest(_manifest())
    assert _ingest(_manifest()) is None  # same content hash -> no new event


def test_ingest_changed_manifest_appends_new_version():
    first = _ingest(_manifest(("s1",)))
    second = _ingest(_manifest(("s1", "s2")))
    assert first is not None and second is not None
    rebuild_data_lineage_view()
    assert get_manifest("TestRepo")["data"]["step_count"] == 2
    assert len(list_manifests()) == 1


def test_get_manifest_absent_returns_none():
    assert get_manifest("NoSuchRepo") is None
