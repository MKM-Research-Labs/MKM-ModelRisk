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
"""The models a product is built from, and the chain they sit in (Model Map).

A product references models through its ``components`` collection (an analytical
engine, one or more curve/market-data models, …). This derives the graph drawn on
the product's Model Map tab: those component models, the models one hop away that
feed them (the chain the product depends on), the directed feed edges between them,
and any data source two of them share. Derived and stateless — the components,
dependencies and data sources on the records are the truth.
"""
from __future__ import annotations

from typing import Any

from config.governance import PRODUCT_COMPONENTS
from src.governance.model_inventory.chain import all_edges
from src.governance.model_inventory.projection import list_models
from src.governance.model_inventory.sources import source_nodes
from src.governance.product.projection import get_product


def derive_product_map(product_id: str, config=None) -> dict[str, Any] | None:
    """The product's component models plus their one-hop feed neighbourhood.

    ``nodes`` carry ``role`` ("component" — referenced directly by the product — or
    "feed" — pulled in because it feeds a component), a ``terminal`` flag (nothing
    consumes it across the whole estate), and ``retired``. ``links`` are the directed
    feed edges among these nodes; ``shared`` lists the pairs joined by a common data
    source. ``None`` if the product does not exist.
    """
    product = get_product(product_id, config=config)
    if product is None:
        return None
    comps = (product.get("data", {}) or {}).get(PRODUCT_COMPONENTS, []) or []

    # A product's components must resolve even where one has since been
    # hibernated — otherwise the product reads as though the binding vanished.
    models = list_models(config=config, include_retired=True)
    by_id = {m["model_id"]: m for m in models}
    component_ids = []
    for item in comps:
        mid = item.get("model_id")
        if mid and mid in by_id and mid not in component_ids:
            component_ids.append(mid)
    comp_set = set(component_ids)

    edges = all_edges(config=config)
    has_downstream = {a for a, _ in edges}
    # One hop out from the components: the models that feed them or that they feed.
    involved = set(comp_set)
    for a, b in edges:
        if a in comp_set:
            involved.add(b)
        if b in comp_set:
            involved.add(a)
    involved = {mid for mid in involved if mid in by_id}

    nodes = [
        {
            "model_id": mid,
            "name": (by_id[mid].get("data", {}) or {}).get("name", mid),
            "tier": (by_id[mid].get("data", {}) or {}).get("tier"),
            "retired": bool(by_id[mid].get("retired")),
            "role": "component" if mid in comp_set else "feed",
            "terminal": mid not in has_downstream,
        }
        for mid in sorted(involved)
    ]
    links = [{"from": a, "to": b} for a, b in edges if a in involved and b in involved]

    # Data sources drawn above the models they supply — and only above the ones
    # nothing feeds, the same rule as the per-model Connections view, so a source
    # marks where data enters the chain rather than webbing it together. The
    # reasoning is in ``model_inventory.sources``.
    sources = source_nodes(sorted(involved), by_id, edges)

    return {
        "product_id": product_id,
        "product_name": (product.get("data", {}) or {}).get("product", product_id),
        "components": component_ids,
        "nodes": nodes,
        "links": links,
        "sources": sources,
    }
