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
cut rendered on a model's Connections tab: the data sources at the top (each drawn
as a node feeding the models that draw on it), then the models one hop away on the
declared dependency graph — the ones that feed the focus above it, the ones it feeds
below. Terminal-ness — "is this the end of a chain?" — is a property of the focus
here, so a coverage gap (a model nothing consumes) reads at a glance.

Derived and stateless: the ``dependencies`` and ``data_sources`` collections on the
models are the truth; this only re-shapes them around one model.
"""
from __future__ import annotations

from typing import Any

from config.governance import DATA_SOURCES_COLLECTION
from src.governance.model_inventory.chain import all_edges
from src.governance.model_inventory.projection import list_models


def _node(model: dict[str, Any]) -> dict[str, Any]:
    """The compact node the neighbourhood view draws for a related model."""
    data = model.get("data", {}) or {}
    return {
        "model_id": model["model_id"],
        "name": data.get("name", model["model_id"]),
        "tier": data.get("tier"),
        "retired": bool(model.get("retired")),
    }


def _sources(model: dict[str, Any]) -> set[str]:
    """The set of data-source values a model declares it pulls inputs from."""
    items = (model.get("data", {}) or {}).get(DATA_SOURCES_COLLECTION, []) or []
    return {s for s in (item.get("data_source") for item in items) if s}


def derive_neighbourhood(model_id: str, config=None) -> dict[str, Any] | None:
    """The neighbourhood of one model, or ``None`` if the model does not exist.

    ``feeds.upstream`` are the models that feed the focus (they sit above it in a
    chain); ``feeds.downstream`` are the models it feeds. ``terminal`` is true when
    nothing consumes the focus's output — the end of a chain — and ``is_source``
    when nothing feeds it. ``shared_sources`` are models joined to the focus *only*
    by a common data source (a feed neighbour is already drawn as an edge, so it is
    not repeated here); each carries the ``shared`` source list that connects them.
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

    focus_sources = _sources(focus)
    # Data sources are drawn as nodes upstream of the models that draw on them: each
    # source links down to the focus and to any of its upstream models that use it.
    # Scoping to the focus + its dependencies keeps a ubiquitous source (e.g. every
    # model on "Simulated") from webbing the whole estate together.
    scope_ids = [model_id] + upstream_ids
    src_map: dict[str, set[str]] = {}
    for mid in scope_ids:
        for name in _sources(by_id[mid]):
            src_map.setdefault(name, set()).add(mid)
    sources = [{"name": name, "models": sorted(ids)} for name, ids in sorted(src_map.items())]

    return {
        "focus": {
            **_node(focus),
            "vendor": (focus.get("data", {}) or {}).get("vendor"),
            "data_sources": sorted(focus_sources),
            "terminal": not downstream_ids,
            "is_source": not upstream_ids,
        },
        "feeds": {
            "upstream": [_node(by_id[i]) for i in upstream_ids if i in by_id],
            "downstream": [_node(by_id[i]) for i in downstream_ids if i in by_id],
        },
        "sources": sources,
    }
