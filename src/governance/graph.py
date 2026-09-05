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


def find_cycle(edges: Iterable[Edge]) -> list[Any]:
    """One cycle, as the path around it, or ``[]`` where the graph is acyclic.

    ``has_cycle`` answers whether; this answers WHICH, because "the model chain has a
    cycle" sends somebody to read the whole graph by hand. The path returned is one
    cycle and not necessarily the only one — fixing it and re-running is the workflow,
    and listing every cycle in a graph that has several is not more useful than naming
    the first.

    Iterative depth-first, with an explicit stack. A chain deep enough to matter is
    deep enough to exhaust the interpreter's, and a monitoring tool that dies with a
    RecursionError on the pathological input it exists to detect is no use at all.
    """
    edge_list = [(a, b) for a, b in edges]
    out: dict[Any, list[Any]] = {}
    for a, b in edge_list:
        out.setdefault(a, []).append(b)
        out.setdefault(b, [])

    UNVISITED, ON_STACK, DONE = 0, 1, 2
    state = {node: UNVISITED for node in out}
    for start in out:
        if state[start] != UNVISITED:
            continue
        # Each frame is (node, iterator position); ``path`` is the route to it.
        stack: list[tuple[Any, int]] = [(start, 0)]
        path: list[Any] = [start]
        state[start] = ON_STACK
        while stack:
            node, index = stack[-1]
            if index < len(out[node]):
                stack[-1] = (node, index + 1)
                nxt = out[node][index]
                if state[nxt] == ON_STACK:
                    return path[path.index(nxt):] + [nxt]
                if state[nxt] == UNVISITED:
                    state[nxt] = ON_STACK
                    stack.append((nxt, 0))
                    path.append(nxt)
            else:
                state[node] = DONE
                stack.pop()
                path.pop()
    return []


def self_loops(edges: Iterable[Edge]) -> list[Edge]:
    """Return the edges whose endpoints are identical (a model depends on itself)."""
    return [(a, b) for a, b in edges if a == b]
