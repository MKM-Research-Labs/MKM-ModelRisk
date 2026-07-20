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
"""Backfill: turn the migrated model chain (a seed snapshot) into native state.

Reads the ingested "string of pearls" and, for each edge whose *both* endpoints are
registered models, declares the dependency and creates the handoff — populating its
compatibility note and field lineage from the chain data. Edges whose models are not
in the inventory are skipped (they must be onboarded first). Idempotent and
re-runnable: existing edges/handoffs/fields are left alone.

Run against the configured ModelRisk database:

    python -m scripts.backfill_chain
"""
from __future__ import annotations

from src.governance.model_chain import get_chain, rebuild_model_chain_view
from src.governance.model_handoff import (
    add_collection_item as handoff_add_item,
    declare_handoff,
    get_handoff,
    handoff_id,
    rebuild_handoff_view,
    update_handoff_field,
)
from src.governance.model_inventory import (
    add_collection_item as declare_dependency,
    list_models,
    rebuild_inventory_view,
)
from src.governance.model_inventory.chain import all_edges

ACTOR = "backfill_chain"


def _seed_field_lineage(hid, link, actor, config) -> None:
    """Add each provider field from the chain as a field-lineage pair. The snapshot
    carries only the provider side, so the consumer field defaults to the same name
    (a starting point the owner can remap); the description becomes the note."""
    handoff = get_handoff(hid, config=config) or {"data": {}}
    seen = {f.get("provider_field") for f in handoff["data"].get("field_lineage", [])}
    for field in link.get("fields", []):
        name = field.get("name")
        if not name or name in seen:
            continue
        handoff_add_item(
            handoff_id=hid, collection="field_lineage", actor=actor, config=config,
            fields={"provider_field": name, "provider_type": field.get("type", ""),
                    "consumer_field": name, "consumer_type": field.get("type", ""),
                    "note": field.get("description", "")},
        )


def backfill(source_repo: str = "PhysicalRisk", *, actor: str = ACTOR, config=None) -> dict:
    """Backfill dependencies + handoffs from the migrated chain. Returns a count summary."""
    rebuild_inventory_view(config=config)
    rebuild_model_chain_view(config=config)
    rebuild_handoff_view(config=config)
    chain = get_chain(source_repo, config=config)
    if chain is None:
        return {"dependencies": 0, "handoffs": 0, "skipped": 0}
    registered = {m["model_id"] for m in list_models(config=config)}
    edges = set(all_edges(config=config))
    declared = handoffs = skipped = 0
    for link in chain["data"]["chain"]["links"]:
        producer, consumer = link.get("from"), link.get("to")
        if producer not in registered or consumer not in registered:
            skipped += 1
            continue
        if (producer, consumer) not in edges:
            declare_dependency(
                model_id=producer, collection="dependencies", actor=actor, config=config,
                fields={"direction": "downstream", "model_id": consumer})
            rebuild_inventory_view(config=config)
            edges.add((producer, consumer))
            declared += 1
        hid = handoff_id(producer, consumer)
        if get_handoff(hid, config=config) is None:
            declare_handoff(from_model=producer, to_model=consumer, actor=actor, config=config)
            rebuild_handoff_view(config=config)
        for field, value in (("compatibility", link.get("compatibility")),
                             ("data_handoff", link.get("data_handoff"))):
            if value:
                update_handoff_field(handoff_id=hid, field=field, value=value, actor=actor, config=config)
        _seed_field_lineage(hid, link, actor, config)
        rebuild_handoff_view(config=config)
        handoffs += 1
    return {"dependencies": declared, "handoffs": handoffs, "skipped": skipped}


def main() -> int:
    from src.database import run_migrations
    run_migrations()
    result = backfill()
    print(f"dependencies declared: {result['dependencies']}, "
          f"handoffs seeded: {result['handoffs']}, "
          f"edges skipped (model not in inventory): {result['skipped']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
