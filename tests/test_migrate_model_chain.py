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
"""The model-chain migration loader — the first component to actually cross.

Proves the loader reads a source repo's ``model_inventory.json``, pushes the chain
through the real ingest contract, and lands it in ``model_chain_view`` — and that
re-running is a no-op. Includes an acceptance run against the *real* PhysicalRisk
chain when that repo is present on the machine.
"""
from __future__ import annotations

import json

import pytest

from scripts.migrate_model_chain import (
    DEFAULT_SOURCE,
    extract_chain,
    load_model_chain,
)
from src.governance.model_chain import get_chain, rebuild_model_chain_view

_INVENTORY = {
    "models": [{"model_id": "A", "name": "a"}, {"model_id": "B", "name": "b"}],
    "model_chain": {
        "description": "A -> B",
        "links": [{"from": "A", "to": "B", "data_handoff": "score"}],
    },
}


def _source(tmp_path, inventory):
    path = tmp_path / "model_inventory.json"
    path.write_text(json.dumps(inventory), encoding="utf-8")
    return path


# --- pure ---

def test_extract_chain_pulls_the_links():
    assert extract_chain(_INVENTORY)["links"][0]["from"] == "A"


def test_extract_chain_without_links_raises():
    with pytest.raises(ValueError):
        extract_chain({"models": []})


# --- the migration itself (DB-backed) ---

def test_migration_lands_the_chain_in_the_view(tmp_path):
    receipt, created = load_model_chain(
        _source(tmp_path, _INVENTORY), source_repo="PhysicalRisk", commit="deadbeef",
    )
    assert created is True
    assert receipt["data"]["summary"]["link_count"] == 1
    rebuild_model_chain_view()
    stored = get_chain("PhysicalRisk")
    assert stored["data"]["link_count"] == 1
    assert stored["data"]["chain"]["links"][0]["to"] == "B"
    # Provenance pins the move to a known source revision.
    assert stored["data"]["provenance"]["commit"] == "deadbeef"


def test_migration_is_idempotent(tmp_path):
    src = _source(tmp_path, _INVENTORY)
    load_model_chain(src, source_repo="PhysicalRisk", commit="deadbeef")
    _, created = load_model_chain(src, source_repo="PhysicalRisk", commit="deadbeef")
    assert created is False  # unchanged content -> no new event


@pytest.mark.skipif(not DEFAULT_SOURCE.is_file(),
                    reason="PhysicalRisk repo not present on this machine")
def test_migrates_the_real_physicalrisk_chain():
    """Acceptance: the actual 'string of pearls' crosses the boundary."""
    receipt, created = load_model_chain(DEFAULT_SOURCE, source_repo="PhysicalRisk")
    assert created is True
    rebuild_model_chain_view()
    stored = get_chain("PhysicalRisk")["data"]
    # The real chain is 11 links across the storm/flood pipeline.
    assert stored["link_count"] == 11
    ids = {l["from"] for l in stored["chain"]["links"]} | {l["to"] for l in stored["chain"]["links"]}
    assert "MKM-SI-001" in ids and "MKM-DE-001" in ids  # Storm Intensity … Delta Engine
