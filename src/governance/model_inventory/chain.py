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
"""The 'string of pearls', derived from declared model dependencies.

ModelRisk cannot *scan* for lineage — it does not hold the repos or know which
models exist until an owner registers them. So the model chain is *declared*: each
model carries a ``dependencies`` collection (``direction`` upstream/downstream +
the related ``model_id``), and the chain is the directed graph those declarations
imply. This module is the read side — it turns declarations into edges and a whole
graph. It is derived and holds no state of its own; the declarations are the truth.
"""
from __future__ import annotations

from typing import Any

from config.governance import DEPENDENCIES_COLLECTION
from src.governance.graph import Edge
from src.governance.model_inventory.projection import list_models

# A downstream dependency of M on R means M feeds R (edge M -> R); an upstream
# dependency of M on R means R feeds M (edge R -> M). The two are reciprocal: if M
# declares "downstream R" and R declares "upstream M" they name the same edge, so
# the graph dedupes them.
_DOWNSTREAM = "downstream"


def edges_for_model(model_id: str, dependency_items) -> list[Edge]:
    """The directed edges one model's ``dependencies`` items contribute."""
    edges: list[Edge] = []
    for item in dependency_items:
        related = item.get("model_id")
        if not related:
            continue
        if item.get("direction") == _DOWNSTREAM:
            edges.append((model_id, related))
        else:
            edges.append((related, model_id))
    return edges


def _model_id(model: dict[str, Any]) -> str:
    return model["model_id"]


def _dependencies(model: dict[str, Any]) -> list[dict[str, Any]]:
    return model.get("data", {}).get(DEPENDENCIES_COLLECTION, []) or []


def all_edges(config=None) -> list[Edge]:
    """Every declared edge across the inventory, deduped (reciprocal declarations
    collapse to one edge). Order is stable for a stable inventory."""
    seen: dict[Edge, None] = {}
    for model in list_models(config=config):
        for edge in edges_for_model(_model_id(model), _dependencies(model)):
            seen.setdefault(edge, None)
    return list(seen)


def derive_chain(config=None) -> dict[str, Any]:
    """The whole graph for the chain screen: every model as a node (flagged if
    hibernated), plus the deduped directed edges the declarations imply."""
    models = list_models(config=config)
    nodes = [
        {
            "model_id": _model_id(m),
            "name": m.get("data", {}).get("name", _model_id(m)),
            "tier": m.get("data", {}).get("tier"),
            "retired": bool(m.get("retired")),
        }
        for m in models
    ]
    links = [{"from": a, "to": b} for a, b in all_edges(config=config)]
    return {"nodes": nodes, "links": links}
