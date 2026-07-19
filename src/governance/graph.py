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
"""Pure directed-graph helpers for the model dependency graph.

Both the ingest-time chain check (a producer pushes a whole 'string of pearls')
and the declaration-time guard (an owner declares one dependency at a time) need
the same invariant: the graph is acyclic. Keeping the topological test here means
one implementation, tested once, feeds both call sites.
"""
from __future__ import annotations

from typing import Any, Iterable

Edge = tuple[Any, Any]


def has_cycle(edges: Iterable[Edge]) -> bool:
    """Return ``True`` if the directed edges contain a cycle (Kahn's algorithm).

    Repeatedly strip nodes with no incoming edges; whatever cannot be stripped
    sits on a cycle. Self-loops (``a -> a``) count as a cycle here — callers that
    want a distinct self-loop message should test for those separately first.
    """
    edge_list = [(a, b) for a, b in edges]
    nodes = {n for edge in edge_list for n in edge}
    incoming = {n: 0 for n in nodes}
    for _, b in edge_list:
        incoming[b] += 1
    ready = [n for n in nodes if incoming[n] == 0]
    seen = 0
    while ready:
        node = ready.pop()
        seen += 1
        for a, b in edge_list:
            if a == node:
                incoming[b] -= 1
                if incoming[b] == 0:
                    ready.append(b)
    return seen != len(nodes)


def self_loops(edges: Iterable[Edge]) -> list[Edge]:
    """Return the edges whose endpoints are identical (a model depends on itself)."""
    return [(a, b) for a, b in edges if a == b]
