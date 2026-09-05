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
"""Lineage carries five kinds of node, two of which the institution does not own.

The chain was a string of pearls between models and every node in it was one. A system
whose harness calls an ML Application as a tool, runs on a foundation model somebody
else versions and reaches an MCP server outside the firm is not describable that way,
and a supply chain you cannot draw is one nobody notices until it moves.
"""
from __future__ import annotations

from config.governance._lineage import (DEFAULT_NODE_KIND, EXTERNAL_NODE_KINDS,
                                        NODE_AI_SYSTEM, NODE_FOUNDATION_MODEL,
                                        NODE_KIND_LABELS, NODE_KIND_RECORD_TYPES,
                                        NODE_KINDS, NODE_MCP_SERVER,
                                        NODE_ML_APPLICATION, NODE_MODEL, is_governed,
                                        node_kind)
from src.governance.graph import find_cycle, has_cycle
from src.ingest._validate import _check_model_chain


# --- The vocabulary -----------------------------------------------------------

def test_all_five_kinds_are_defined_and_labelled():
    assert NODE_KINDS == (NODE_MODEL, NODE_ML_APPLICATION, NODE_AI_SYSTEM,
                          NODE_FOUNDATION_MODEL, NODE_MCP_SERVER)
    assert set(NODE_KIND_LABELS) == set(NODE_KINDS)
    assert set(NODE_KIND_RECORD_TYPES) == set(NODE_KINDS)


def test_two_kinds_are_outside_the_firm_and_open_no_record():
    """A foundation model and an MCP server are dependencies the institution cannot
    review. Offering a link to a record for them would be a lie."""
    assert EXTERNAL_NODE_KINDS == (NODE_FOUNDATION_MODEL, NODE_MCP_SERVER)
    assert not is_governed(NODE_FOUNDATION_MODEL)
    assert not is_governed(NODE_MCP_SERVER)
    for kind in (NODE_MODEL, NODE_ML_APPLICATION, NODE_AI_SYSTEM):
        assert is_governed(kind)


def test_a_node_that_declares_nothing_is_a_model():
    """Every chain pushed before nodes existed is a graph of models, and re-ingesting
    one must not turn its nodes into "unknown"."""
    assert node_kind({}) == DEFAULT_NODE_KIND == NODE_MODEL
    assert node_kind({"id": "M-1"}) == NODE_MODEL


def test_a_declared_kind_is_read_whatever_case_it_arrives_in():
    assert node_kind({"kind": "ai_system"}) == NODE_AI_SYSTEM
    assert node_kind({"kind": " Mcp_Server "}) == NODE_MCP_SERVER


# --- Chains that mix them -----------------------------------------------------

def test_chain_mixing_all_five_node_types_builds():
    chain = {
        "nodes": [
            {"id": "FM-1", "kind": NODE_FOUNDATION_MODEL, "label": "claude-opus-4"},
            {"id": "MCP-1", "kind": NODE_MCP_SERVER, "label": "policy-lookup"},
            {"id": "AIS-1", "kind": NODE_AI_SYSTEM},
            {"id": "MLA-1", "kind": NODE_ML_APPLICATION},
            {"id": "M-1", "kind": NODE_MODEL},
        ],
        "links": [
            {"from": "FM-1", "to": "AIS-1"},
            {"from": "MCP-1", "to": "AIS-1"},
            {"from": "MLA-1", "to": "AIS-1"},
            {"from": "M-1", "to": "MLA-1"},
        ],
    }
    assert _check_model_chain(chain) == []


def test_ml_app_as_tool_of_agentic_system():
    """The spec's own case: an agentic system's harness calls a fraud ML Application as
    a tool. Before node kinds, this was two models with an arrow between them and the
    graph could not say that one of them can act."""
    chain = {
        "nodes": [
            {"id": "AIS-FRAUD", "kind": NODE_AI_SYSTEM, "label": "Fraud triage agent"},
            {"id": "MLA-FRAUD", "kind": NODE_ML_APPLICATION,
             "label": "Fraud probability classifier"},
        ],
        "links": [{"from": "MLA-FRAUD", "to": "AIS-FRAUD",
                   "data_handoff": "fraud probability, per claim"}],
    }
    assert _check_model_chain(chain) == []
    kinds = {n["id"]: node_kind(n) for n in chain["nodes"]}
    assert kinds["MLA-FRAUD"] == NODE_ML_APPLICATION
    assert kinds["AIS-FRAUD"] == NODE_AI_SYSTEM


def test_a_chain_with_no_nodes_declared_is_still_valid():
    """Backwards compatibility is the point: the estate's existing chains declare
    none."""
    assert _check_model_chain({"links": [{"from": "A", "to": "B"}]}) == []


def test_a_misspelt_kind_is_refused_rather_than_treated_as_a_model():
    """Silently defaulting a typo is how a foundation model disappears into the estate
    as something the firm believes it governs."""
    errors = _check_model_chain({
        "nodes": [{"id": "FM-1", "kind": "FOUNDATION-MODEL"}],
        "links": [],
    })
    assert len(errors) == 1
    assert "unknown kind" in errors[0] and "FM-1" in errors[0]


def test_a_link_to_an_undeclared_node_is_refused_once_nodes_are_declared():
    """Declaring nodes is opt-in; having declared them, the graph must be complete, or
    the diagram silently omits a dependency somebody wrote down."""
    errors = _check_model_chain({
        "nodes": [{"id": "A", "kind": NODE_MODEL}],
        "links": [{"from": "A", "to": "GHOST"}],
    })
    assert any("GHOST" in e for e in errors)


# --- Cycles, by name ----------------------------------------------------------

def test_cycle_rejected_by_name():
    """"The chain has a cycle" sends somebody to read the whole graph by hand. The
    path is what they were going to look for."""
    errors = _check_model_chain({"links": [
        {"from": "A", "to": "B"}, {"from": "B", "to": "C"}, {"from": "C", "to": "A"},
    ]})
    assert len(errors) == 1
    assert "A -> B -> C -> A" in errors[0]


def test_a_self_loop_is_named_as_itself_not_as_a_cycle():
    errors = _check_model_chain({"links": [{"from": "A", "to": "A"}]})
    assert any("cannot depend on itself" in e for e in errors)


def test_find_cycle_agrees_with_has_cycle_and_survives_a_deep_chain():
    """Iterative, with an explicit stack: a tool that dies with a RecursionError on the
    pathological input it exists to detect is no use at all."""
    deep = [(str(i), str(i + 1)) for i in range(5000)]
    assert find_cycle(deep) == [] and has_cycle(deep) is False
    looped = deep + [("5000", "0")]
    assert find_cycle(looped) and has_cycle(looped) is True
