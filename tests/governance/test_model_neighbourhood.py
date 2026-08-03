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
"""Tests for the per-model neighbourhood derivation (feeds + shared sources)."""
from __future__ import annotations

from src.governance.model_inventory import (
    add_collection_item,
    derive_neighbourhood,
    rebuild_inventory_view,
    register_model,
)
from src.governance.reference import add_option


def _feed(model_id: str, direction: str, related: str) -> None:
    add_collection_item(model_id=model_id, collection="dependencies",
                        fields={"direction": direction, "model_id": related}, actor="a")


def _source(model_id: str, value: str) -> None:
    add_collection_item(model_id=model_id, collection="data_sources",
                        fields={"data_source": value}, actor="a")


def _build_estate() -> None:
    for mid, name in [("M-A", "Yield Curve"), ("M-B", "Vol Surface"),
                      ("M-FOCUS", "Valuation Engine"), ("M-C", "Capital Reserve"),
                      ("M-SIB", "FX Exposure")]:
        register_model(model_id=mid, name=name, actor="a")
    # The dependency guard reads the model view, so refresh it (the app rebuilds
    # after every write) before declaring cross-model edges.
    rebuild_inventory_view()
    # A and B feed FOCUS; FOCUS feeds C. So FOCUS is mid-chain, C is terminal.
    _feed("M-FOCUS", "upstream", "M-A")
    _feed("M-FOCUS", "upstream", "M-B")
    _feed("M-FOCUS", "downstream", "M-C")
    # Bloomberg is shared by FOCUS, its downstream C, and the otherwise-unconnected SIB.
    add_option(list_name="data_source", fields={"value": "Bloomberg"}, actor="admin")
    _source("M-FOCUS", "Bloomberg")
    _source("M-C", "Bloomberg")
    _source("M-SIB", "Bloomberg")
    # derive_neighbourhood reads the view too — refresh it after all the writes.
    rebuild_inventory_view()


def test_focus_reports_feeds_and_chain_position():
    _build_estate()
    n = derive_neighbourhood("M-FOCUS")
    assert [m["model_id"] for m in n["feeds"]["upstream"]] == ["M-A", "M-B"]
    assert [m["model_id"] for m in n["feeds"]["downstream"]] == ["M-C"]
    # Mid-chain: consumed by C and fed by A/B.
    assert n["focus"]["terminal"] is False
    assert n["focus"]["is_source"] is False
    assert n["focus"]["data_sources"] == ["Bloomberg"]


def test_sources_are_nodes_scoped_to_focus_and_upstream():
    _build_estate()
    n = derive_neighbourhood("M-FOCUS")
    # Bloomberg is drawn as a source node linking to the focus and any upstream model
    # that uses it. FOCUS uses Bloomberg; its upstream A/B do not; C (downstream) is
    # out of scope. So the source points at the focus only.
    by_name = {s["name"]: s for s in n["sources"]}
    assert set(by_name) == {"Bloomberg"}
    assert by_name["Bloomberg"]["models"] == ["M-FOCUS"]


def test_source_links_to_upstream_that_uses_it():
    _build_estate()
    # Give an upstream model (A) the same source, so it should appear on the edge too.
    _source("M-A", "Bloomberg")
    rebuild_inventory_view()
    n = derive_neighbourhood("M-FOCUS")
    by_name = {s["name"]: s for s in n["sources"]}
    assert by_name["Bloomberg"]["models"] == ["M-A", "M-FOCUS"]


def test_terminal_model_has_no_downstream():
    _build_estate()
    n = derive_neighbourhood("M-C")
    assert n["focus"]["terminal"] is True
    assert [m["model_id"] for m in n["feeds"]["upstream"]] == ["M-FOCUS"]
    assert n["feeds"]["downstream"] == []


def test_unknown_model_returns_none():
    assert derive_neighbourhood("ghost") is None
