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
"""Where data enters a chain: the data-source nodes a lineage picture draws.

A model's ``data_sources`` collection says which external feeds it pulls on. Drawn
naively — one node per source, an arrow to every model that declares it — that
states something the record does not: on the PRS view a "Simulated" arrow into
MKM-BRF-001 reads as *BRF starts from simulated data*, when what feeds BRF is
MKM-BRI-001, one hop further up and off that screen. A source declared across a
whole estate (an unset default, usually) webs every picture together that way.

So a source is only drawn against a model nothing feeds — the point where data
actually enters the chain. A mid-chain model's own declaration still stands on its
record and in the register under the canvas; it is the *arrow* that would be a
misstatement, so only the arrow goes.
"""
from __future__ import annotations

from typing import Any, Iterable

from config.governance import DATA_SOURCES_COLLECTION
from src.governance.graph import Edge


def declared_sources(model: dict[str, Any]) -> set[str]:
    """The set of data-source values a model declares it pulls inputs from."""
    items = (model.get("data", {}) or {}).get(DATA_SOURCES_COLLECTION, []) or []
    return {s for s in (item.get("data_source") for item in items) if s}


def entry_points(model_ids: Iterable[str], edges: Iterable[Edge]) -> list[str]:
    """Those of ``model_ids`` that nothing feeds — where a chain starts.

    Judged against every declared edge, not only the ones a given picture draws: a
    model is no less fed for its feeder being off-screen.
    """
    fed = {b for _, b in edges}
    return [mid for mid in model_ids if mid not in fed]


def source_nodes(model_ids: Iterable[str], by_id: dict[str, Any],
                 edges: Iterable[Edge]) -> list[dict[str, Any]]:
    """The data-source nodes to draw above ``model_ids``, each with the models it
    links down to — the chain-starting ones only (see the module docstring)."""
    src_map: dict[str, set[str]] = {}
    for mid in entry_points(model_ids, edges):
        model = by_id.get(mid)
        if model is None:
            continue
        for name in declared_sources(model):
            src_map.setdefault(name, set()).add(mid)
    return [{"name": name, "models": sorted(ids)} for name, ids in sorted(src_map.items())]
