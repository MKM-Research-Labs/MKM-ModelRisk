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
"""Model-chain aggregate: pure fold/rules and DB-backed command + projection."""
from __future__ import annotations

import pytest

from src.governance.errors import DomainError
from src.governance.model_chain import (
    get_chain,
    ingest_model_chain,
    list_chains,
    rebuild_model_chain_view,
)
from src.governance.model_chain._rules import decide_ingest
from src.governance.model_chain._state import EVENT_INGESTED, apply, initial_state
from src.ingest._envelope import content_hash

PROV = {
    "source_repo": "TestRepo", "commit": "abc123", "producer": "migrate_model_chain",
    "producer_version": "1.0.0", "generated_at": "2026-07-17T00:00:00Z",
}


def _chain(links=(("A", "B"),)):
    return {"description": "test chain",
            "links": [{"from": a, "to": b, "data_handoff": "x"} for a, b in links]}


# --- pure ---

def test_apply_ingested_sets_state():
    payload = {"chain": _chain(), "content_hash": "h", "provenance": PROV}
    state = apply(initial_state(), EVENT_INGESTED, payload)
    assert state.exists and state.content_hash == "h"


def test_apply_ignores_unknown_event():
    assert apply(initial_state(), "Whatever", {}) == initial_state()


def test_decide_ingest_builds_link_count():
    event_type, payload = decide_ingest(
        initial_state(), chain=_chain((("A", "B"), ("B", "C"))),
        provenance=PROV, content_hash="h",
    )
    assert event_type == EVENT_INGESTED
    assert payload["link_count"] == 2


def test_decide_ingest_rejects_non_dict():
    with pytest.raises(DomainError):
        decide_ingest(initial_state(), chain=[], provenance=PROV, content_hash="h")


# --- DB-backed ---

def _ingest(chain):
    return ingest_model_chain(
        source_repo="TestRepo", chain=chain, provenance=PROV,
        content_hash=content_hash(chain), actor="ingest:TestRepo",
    )


def test_ingest_new_chain_appends_and_projects():
    event = _ingest(_chain())
    assert event is not None
    rebuild_model_chain_view()
    doc = get_chain("TestRepo")
    assert doc["content_hash"] == content_hash(_chain())
    assert doc["data"]["link_count"] == 1


def test_ingest_identical_chain_is_idempotent():
    _ingest(_chain())
    assert _ingest(_chain()) is None  # same content hash -> no new event


def test_ingest_changed_chain_appends_new_version():
    first = _ingest(_chain((("A", "B"),)))
    second = _ingest(_chain((("A", "B"), ("B", "C"))))
    assert first is not None and second is not None
    rebuild_model_chain_view()
    assert get_chain("TestRepo")["data"]["link_count"] == 2
    assert len(list_chains()) == 1


def test_get_chain_absent_returns_none():
    assert get_chain("NoSuchRepo") is None
