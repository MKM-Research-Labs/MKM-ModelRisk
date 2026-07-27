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

"""Register MKM-EF-001 (Event Frequency Model) into the ModelRisk inventory.

The other 24 PhysicalRisk models were bulk-migrated from the source
``model_inventory.json`` by ``migrate_phys``. MKM-EF-001 post-dates that
inventory and was never added to it, so it is registered directly here through
the same governance command API rather than by editing the source file.

Idempotent: an already-registered model is left untouched, and each chain edge
is added only if absent, so the script is safe to re-run.

Run as:  python -m scripts.register_ef001

The governance content is not invented for the demo. Every assumption,
limitation and weakness below is a finding from building and validating the
model — see ``PhysicalRisk/docs/storm_freq/frequency_layer_definition_and_plan_v2.md``.
The two that matter most for effective challenge:

- lambda is a per-catchment engineering-judgement seed, and NOTHING in the
  platform currently validates it (both the synthetic-record and the
  per-gauge-extraction validation routes are circular — plan §5).
- the reprice it produces is real and material (0.35-0.56x downward on flood),
  but rests on that unvalidated lambda and on population weights that are also
  owner judgement.
"""
from __future__ import annotations

from src.governance.errors import DomainError
from src.governance.model_inventory import (
    add_collection_item,
    derive_chain,
    get_model,
    rebuild_inventory_view,
    register_model,
)

from scripts._ef001_data import (ASSUMPTIONS, CHAIN_EDGES, FIELDS, LIMITATIONS,
                                 MODEL_ID, WEAKNESSES)

ACTOR = "register_ef001"

def _register(config=None) -> bool:
    """Register the model with its scalar fields and collections.

    Returns True if it was registered, False if it already existed.
    """
    if get_model(MODEL_ID, config=config) is not None:
        return False
    register_model(
        model_id=MODEL_ID, name=FIELDS["name"], actor=ACTOR, config=config,
        fields=FIELDS,
        reason="Register MKM-EF-001 Event Frequency Model (Stage 5 governance)",
    )
    for assumption in ASSUMPTIONS:
        add_collection_item(model_id=MODEL_ID, collection="assumptions",
                            fields=assumption, actor=ACTOR, config=config)
    for limitation in LIMITATIONS:
        add_collection_item(model_id=MODEL_ID, collection="limitations",
                            fields=limitation, actor=ACTOR, config=config)
    for weakness in WEAKNESSES:
        add_collection_item(model_id=MODEL_ID, collection="model_weaknesses",
                            fields={"description": weakness}, actor=ACTOR, config=config)
    return True


def _declare_chain(config=None) -> int:
    """Declare the two chain edges around MKM-EF-001, skipping any that exist.

    Returns the number of edges newly declared.
    """
    existing = {(link["from"], link["to"]) for link in derive_chain(config=config)["links"]}
    declared = 0
    for producer, consumer in CHAIN_EDGES:
        if (producer, consumer) in existing:
            continue
        if get_model(producer, config=config) is None or get_model(consumer, config=config) is None:
            continue
        try:
            add_collection_item(
                model_id=producer, collection="dependencies", actor=ACTOR, config=config,
                fields={"direction": "downstream", "model_id": consumer})
            declared += 1
        except DomainError:
            continue  # a cycle the guard rejects — leave the chain intact
    return declared


def register(config=None) -> dict:
    """Register MKM-EF-001 and place it in the model chain.

    Returns a summary of what was done.
    """
    registered = _register(config=config)
    # Rebuild before declaring the chain: derive_chain and the get_model guards
    # in _declare_chain read the inventory view, which must reflect the just-
    # registered model or both new edges are silently skipped.
    rebuild_inventory_view(config=config)
    declared = _declare_chain(config=config)
    rebuild_inventory_view(config=config)
    return {"registered": registered, "edges_declared": declared}


def main() -> int:
    from src.database import run_migrations

    run_migrations()
    result = register()
    if result["registered"]:
        print(f"MKM-EF-001 registered with "
              f"{len(ASSUMPTIONS)} assumptions, {len(LIMITATIONS)} limitations, "
              f"{len(WEAKNESSES)} weaknesses.")
    else:
        print("MKM-EF-001 already registered; left untouched.")
    print(f"chain edges declared: {result['edges_declared']} "
          f"(MKM-GH-001 -> MKM-EF-001 -> MKM-PR-001)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
