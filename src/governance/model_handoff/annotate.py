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

"""Handoff detail layered onto a neighbourhood graph.

The neighbourhood (``model_inventory.neighbourhood``) knows which arrows exist and
who declared them; what *crosses* an arrow is the handoff's business. Annotating
here rather than there keeps the dependency one-way — the handoff aggregate already
reads the inventory to validate an edge, and the reverse would be a cycle.
"""
from __future__ import annotations

from typing import Any

from src.governance.model_handoff.commands import handoff_id
from src.governance.model_handoff.projection import derive_status, list_handoffs


def _summary(data: dict[str, Any] | None) -> dict[str, Any]:
    """What an arrow needs to say for itself: whether a handoff has been declared,
    how many fields cross it, and where its compatibility sign-off has got to."""
    return {
        "declared": data is not None,
        "field_count": len((data or {}).get("field_lineage") or []),
        "status": derive_status(data) if data is not None else None,
    }


def _index(config=None) -> dict[str, dict[str, Any]]:
    """Every declared handoff by id. One read serves a whole graph's worth of arrows."""
    return {h["handoff_id"]: (h.get("data") or {}) for h in list_handoffs(config=config)}


def annotate_neighbourhood(neighbourhood: dict[str, Any], config=None) -> dict[str, Any]:
    """Add a ``handoff`` summary to every edge in a neighbourhood, in place.

    A neighbour with no ``edge`` (an older payload) is left alone rather than invented.
    """
    handoffs = _index(config=config)
    for direction in ("upstream", "downstream"):
        for node in neighbourhood.get("feeds", {}).get(direction, []):
            edge = node.get("edge")
            if edge:
                edge["handoff"] = _summary(handoffs.get(handoff_id(edge["from"], edge["to"])))
    return neighbourhood


def annotate_links(links: list[dict[str, Any]], config=None) -> list[dict[str, Any]]:
    """Add a ``handoff`` summary to each ``{"from": .., "to": ..}`` link, in place.

    The shape the whole-estate chain and the product model map both use, so an arrow
    says the same thing about what crosses it wherever it is drawn.
    """
    handoffs = _index(config=config)
    for link in links:
        link["handoff"] = _summary(handoffs.get(handoff_id(link["from"], link["to"])))
    return links
