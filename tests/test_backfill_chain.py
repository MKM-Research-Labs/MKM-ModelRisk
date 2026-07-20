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
"""The chain backfill — turn the migrated chain seed into native declarations.

Reads the ingested chain and, for edges whose both endpoints are registered,
declares the dependency and seeds the handoff (compatibility + field lineage).
Edges whose models are absent are skipped; the whole thing is idempotent.
"""
from __future__ import annotations

from scripts.backfill_chain import backfill
from src.governance.model_chain import ingest_model_chain, rebuild_model_chain_view
from src.governance.model_handoff import get_handoff_for_edge
from src.governance.model_inventory import derive_chain, register_model, rebuild_inventory_view
from src.ingest._envelope import content_hash

PROV = {
    "source_repo": "TestRepo", "commit": "abc123", "producer": "migrate_model_chain",
    "producer_version": "1.0.0", "generated_at": "2026-07-20T00:00:00Z",
}


def _register(*ids):
    for model_id in ids:
        register_model(model_id=model_id, name=model_id, actor="alice")
    rebuild_inventory_view()


def _ingest_chain(links):
    chain = {"links": links}
    ingest_model_chain(source_repo="TestRepo", chain=chain, provenance=PROV,
                       content_hash=content_hash(chain), actor="test")
    rebuild_model_chain_view()


def test_backfill_declares_dependency_and_seeds_the_handoff():
    _register("A", "B")
    _ingest_chain([{"from": "A", "to": "B", "compatibility": "units align",
                    "data_handoff": "the score",
                    "fields": [{"name": "s", "type": "float", "description": "the score"}]}])
    assert backfill(source_repo="TestRepo") == {"dependencies": 1, "handoffs": 1, "skipped": 0}

    assert {"from": "A", "to": "B"} in derive_chain()["links"]
    handoff = get_handoff_for_edge("A", "B")["data"]
    assert handoff["compatibility"] == "units align" and handoff["data_handoff"] == "the score"
    field = handoff["field_lineage"][0]
    assert field["provider_field"] == "s" and field["consumer_field"] == "s"
    assert field["provider_type"] == "float" and field["note"] == "the score"


def test_backfill_skips_edges_with_an_unregistered_model():
    _register("A")  # B is not in the inventory
    _ingest_chain([{"from": "A", "to": "B"}])
    assert backfill(source_repo="TestRepo") == {"dependencies": 0, "handoffs": 0, "skipped": 1}
    assert derive_chain()["links"] == []


def test_backfill_is_idempotent():
    _register("A", "B")
    _ingest_chain([{"from": "A", "to": "B", "fields": [{"name": "s"}]}])
    backfill(source_repo="TestRepo")
    # A second run adds nothing new: the edge exists and the field is not duplicated.
    assert backfill(source_repo="TestRepo") == {"dependencies": 0, "handoffs": 1, "skipped": 0}
    assert len(get_handoff_for_edge("A", "B")["data"]["field_lineage"]) == 1


def test_backfill_without_a_migrated_chain_is_a_no_op():
    assert backfill(source_repo="AbsentRepo") == {"dependencies": 0, "handoffs": 0, "skipped": 0}
