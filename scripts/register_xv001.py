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

"""Register MKM-XV-001 (PRS XVA Model) into the ModelRisk inventory.

A new model, designed in ``PhysicalRisk/docs/xva/project_plan.md`` and agreed
on 2026-10-09: credit, funding and capital valuation adjustments on the
Physical Risk Swap, after Green (2015). Registered at WP0, before anything is
built, so that the full validation exercise is tracked from the start.
Mirrors ``register_ef001``.

Idempotent: an already-registered model is left untouched, and each chain edge
is added only if absent, so the script is safe to re-run.

Run as:  python -m scripts.register_xv001

The two facts that matter most for effective challenge:

- the regulatory treatment of a PRS (derivative or insurance, SA-CCR asset
  class, FRTB residual-risk add-on) is undecided, and KVA depends on it;
- counterparty, funding and CSA inputs are synthetic on the platform today.
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

from scripts._xv001_data import (ASSUMPTIONS, CHAIN_EDGES, FIELDS, LIMITATIONS,
                                 MODEL_ID, WEAKNESSES)

ACTOR = "register_xv001"

def _register(config=None) -> bool:
    """Register the model with its scalar fields and collections.

    Returns True if it was registered, False if it already existed.
    """
    if get_model(MODEL_ID, config=config) is not None:
        return False
    register_model(
        model_id=MODEL_ID, name=FIELDS["name"], actor=ACTOR, config=config,
        fields=FIELDS,
        reason="Register MKM-XV-001 PRS XVA Model (WP0, design agreed 2026-10-09)",
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
    """Declare the chain edges around MKM-XV-001, skipping any that exist.

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
    """Register MKM-XV-001 and place it in the model chain.

    Returns a summary of what was done.
    """
    registered = _register(config=config)
    # Rebuild before declaring the chain: derive_chain and the get_model guards
    # in _declare_chain read the inventory view, which must reflect the just-
    # registered model or the new edges are silently skipped.
    rebuild_inventory_view(config=config)
    declared = _declare_chain(config=config)
    rebuild_inventory_view(config=config)
    return {"registered": registered, "edges_declared": declared}


def main() -> int:
    from src.database import run_migrations

    run_migrations()
    result = register()
    if result["registered"]:
        print(f"MKM-XV-001 registered with "
              f"{len(ASSUMPTIONS)} assumptions, {len(LIMITATIONS)} limitations, "
              f"{len(WEAKNESSES)} weaknesses.")
    else:
        print("MKM-XV-001 already registered; left untouched.")
    print(f"chain edges declared: {result['edges_declared']} "
          f"(MKM-PR-001, MKM-EF-001 -> MKM-XV-001 -> MKM-TD-001)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
