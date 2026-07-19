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
"""Declared model dependencies: the derived 'string of pearls' and the guard.

Lineage is declared, not scanned — each model owns a ``dependencies`` collection
and the chain is the directed graph those declarations imply. These tests cover
the derivation (direction resolution + reciprocal dedup) and the declaration-time
guard (unknown model, self-dependency, and cycles are refused).
"""
from __future__ import annotations

import pytest

from src.governance.model_inventory import (
    DomainError,
    add_collection_item,
    derive_chain,
    rebuild_inventory_view,
    register_model,
)
from src.governance.model_inventory.chain import edges_for_model

DEPS = "dependencies"


def _register(model_id, name=None):
    register_model(model_id=model_id, name=name or model_id, actor="alice")


def _declare(model_id, direction, related):
    """Declare one dependency, then refresh the read model (as the web layer does
    after every command) so the next declaration's guard sees this edge."""
    add_collection_item(
        model_id=model_id, collection=DEPS,
        fields={"direction": direction, "model_id": related}, actor="alice",
    )
    rebuild_inventory_view()


# --- pure edge resolution ---

def test_downstream_points_away_from_the_declaring_model():
    assert edges_for_model("M", [{"direction": "downstream", "model_id": "R"}]) == [("M", "R")]


def test_upstream_points_into_the_declaring_model():
    assert edges_for_model("M", [{"direction": "upstream", "model_id": "R"}]) == [("R", "M")]


def test_item_without_a_related_model_is_ignored():
    assert edges_for_model("M", [{"direction": "downstream", "model_id": ""}]) == []


# --- derivation from declarations ---

def test_derive_chain_builds_nodes_and_links():
    _register("A")
    _register("B")
    rebuild_inventory_view()
    _declare("A", "downstream", "B")  # A feeds B
    chain = derive_chain()
    assert {n["model_id"] for n in chain["nodes"]} == {"A", "B"}
    assert chain["links"] == [{"from": "A", "to": "B"}]


def test_reciprocal_declarations_collapse_to_one_edge():
    _register("A")
    _register("B")
    rebuild_inventory_view()
    _declare("A", "downstream", "B")  # A -> B
    _declare("B", "upstream", "A")    # also A -> B
    chain = derive_chain()
    assert chain["links"] == [{"from": "A", "to": "B"}]


def test_hibernated_models_are_flagged_on_their_node():
    _register("A")
    rebuild_inventory_view()
    node = next(n for n in derive_chain()["nodes"] if n["model_id"] == "A")
    assert node["retired"] is False


# --- the declaration-time guard ---

def test_declaring_a_dependency_on_an_unknown_model_is_refused():
    _register("A")
    rebuild_inventory_view()
    with pytest.raises(DomainError, match="unknown related model"):
        add_collection_item(
            model_id="A", collection=DEPS,
            fields={"direction": "downstream", "model_id": "ghost"}, actor="alice",
        )


def test_a_model_cannot_depend_on_itself():
    _register("A")
    rebuild_inventory_view()
    with pytest.raises(DomainError, match="cannot depend on itself"):
        add_collection_item(
            model_id="A", collection=DEPS,
            fields={"direction": "downstream", "model_id": "A"}, actor="alice",
        )


def test_a_dependency_that_closes_a_cycle_is_refused():
    _register("A")
    _register("B")
    rebuild_inventory_view()
    _declare("A", "downstream", "B")  # A -> B
    with pytest.raises(DomainError, match="cycle"):
        add_collection_item(  # B -> A would close the loop
            model_id="B", collection=DEPS,
            fields={"direction": "downstream", "model_id": "A"}, actor="alice",
        )


def test_a_longer_cycle_is_refused():
    for m in ("A", "B", "C"):
        _register(m)
    rebuild_inventory_view()
    _declare("A", "downstream", "B")  # A -> B
    _declare("B", "downstream", "C")  # B -> C
    with pytest.raises(DomainError, match="cycle"):
        add_collection_item(  # C -> A closes A -> B -> C -> A
            model_id="C", collection=DEPS,
            fields={"direction": "downstream", "model_id": "A"}, actor="alice",
        )


def test_a_valid_extra_edge_is_accepted():
    for m in ("A", "B", "C"):
        _register(m)
    rebuild_inventory_view()
    _declare("A", "downstream", "B")
    _declare("B", "downstream", "C")  # A -> B -> C, still acyclic
    chain = derive_chain()
    assert {"from": "A", "to": "B"} in chain["links"]
    assert {"from": "B", "to": "C"} in chain["links"]
