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
"""The pure directed-graph helpers behind the model-chain acyclicity check."""
from __future__ import annotations

from src.governance.graph import has_cycle, self_loops


def test_empty_graph_is_acyclic():
    assert has_cycle([]) is False


def test_linear_chain_is_acyclic():
    assert has_cycle([("A", "B"), ("B", "C"), ("C", "D")]) is False


def test_diamond_is_acyclic():
    # A fans out to B and C, both feed D — a DAG, not a cycle.
    assert has_cycle([("A", "B"), ("A", "C"), ("B", "D"), ("C", "D")]) is False


def test_two_node_cycle_is_detected():
    assert has_cycle([("A", "B"), ("B", "A")]) is True


def test_longer_cycle_is_detected():
    assert has_cycle([("A", "B"), ("B", "C"), ("C", "A")]) is True


def test_self_loop_counts_as_a_cycle():
    assert has_cycle([("A", "A")]) is True


def test_self_loops_lists_only_the_reflexive_edges():
    assert self_loops([("A", "A"), ("A", "B"), ("C", "C")]) == [("A", "A"), ("C", "C")]


def test_self_loops_empty_when_none():
    assert self_loops([("A", "B"), ("B", "C")]) == []
