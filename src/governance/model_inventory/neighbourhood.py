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
"""One model's neighbourhood: its data sources, what feeds it, and what it feeds.

The chain screen (see ``chain.py``) shows the whole estate. This is the per-model
cut rendered on a model's Connections tab: the models one hop away on the declared
dependency graph — the ones that feed the focus above it, the ones it feeds below —
and, above them, the focus's data sources, drawn only where the focus starts a chain
(see ``sources.py``). Terminal-ness — "is this the end of a chain?" — is a property
of the focus here, so a coverage gap (a model nothing consumes) reads at a glance.

Derived and stateless: the ``dependencies`` and ``data_sources`` collections on the
models are the truth; this only re-shapes them around one model.
"""
from __future__ import annotations

from typing import Any

from src.governance.model_inventory.chain import all_edges, declarations_by_edge
from src.governance.model_inventory.projection import list_models
from src.governance.model_inventory.sources import declared_sources, source_nodes


def _node(model: dict[str, Any]) -> dict[str, Any]:
    """The compact node the neighbourhood view draws for a related model."""
    data = model.get("data", {}) or {}
    return {
        "model_id": model["model_id"],
        "name": data.get("name", model["model_id"]),
        "tier": data.get("tier"),
        "retired": bool(model.get("retired")),
    }


def _edge_detail(edge, declarations) -> dict[str, Any]:
    """What the graph needs to treat one arrow as something you can act on: which
    model's ``dependencies`` item put it there. An edge can be declared from either
    end, so withdrawing it may mean touching two models.

    What *crosses* the edge is the handoff's business, and the handoff aggregate
    already depends on this one — ``model_handoff.annotate`` layers it on top rather
    than this module reaching back the other way.
    """
    return {"from": edge[0], "to": edge[1], "declared_by": declarations.get(edge, [])}


def derive_neighbourhood(model_id: str, config=None) -> dict[str, Any] | None:
    """The neighbourhood of one model, or ``None`` if the model does not exist.

    ``feeds.upstream`` are the models that feed the focus (they sit above it in a
    chain); ``feeds.downstream`` are the models it feeds. ``terminal`` is true when
    nothing consumes the focus's output — the end of a chain — and ``is_source``
    when nothing feeds it. ``sources`` are the data sources drawn above the picture —
    the focus's own, and only where it is a chain start, so a source never reads as a
    second origin for a model another model already supplies.
    """
    # A model's own neighbourhood, including a hibernated one: this view has to
    # render for the very model somebody is looking at, and a neighbour that has
    # been retired is a fact about this model, not a gap to hide.
    models = list_models(config=config, include_retired=True)
    by_id = {m["model_id"]: m for m in models}
    focus = by_id.get(model_id)
    if focus is None:
        return None

    edges = all_edges(config=config)
    upstream_ids = sorted({a for a, b in edges if b == model_id})
    downstream_ids = sorted({b for a, b in edges if a == model_id})
    declarations = declarations_by_edge(config=config)

    # The tab shows one hop either side of the focus, and a data source only where
    # the focus is the top of the stack — nothing feeds it, so an external feed is
    # what starts it. Drawn against a model that another model feeds, a source reads
    # as a second origin the record never declared (see ``sources.py``), which is how
    # a blanket "Simulated" ends up claiming to supply half an estate.
    sources = source_nodes([model_id], by_id, edges)

    return {
        "focus": {
            **_node(focus),
            "vendor": (focus.get("data", {}) or {}).get("vendor"),
            "data_sources": sorted(declared_sources(focus)),
            "terminal": not downstream_ids,
            "is_source": not upstream_ids,
        },
        "feeds": {
            "upstream": [{**_node(by_id[i]), "edge": _edge_detail((i, model_id), declarations)}
                         for i in upstream_ids if i in by_id],
            "downstream": [{**_node(by_id[i]), "edge": _edge_detail((model_id, i), declarations)}
                           for i in downstream_ids if i in by_id],
        },
        "sources": sources,
    }
