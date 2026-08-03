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
"""Tests for the product Model Map derivation (components + feed chain + sources)."""
from __future__ import annotations

from config.governance import PRODUCT_COMPONENTS
from src.governance.model_inventory import (
    add_collection_item as add_model_item,
    rebuild_inventory_view,
    register_model,
)
from src.governance.product import (
    add_collection_item as add_product_item,
    derive_product_map,
    rebuild_product_view,
    register_product,
)
from src.governance.reference import add_option


def _build():
    for mid in ("M-AN", "M-CV", "M-UP"):
        register_model(model_id=mid, name=mid + " model", actor="a")
    rebuild_inventory_view()
    # M-UP feeds the analytical component M-AN.
    add_model_item(model_id="M-AN", collection="dependencies",
                   fields={"direction": "upstream", "model_id": "M-UP"}, actor="a")
    # Bloomberg supplies M-AN and its upstream M-UP (but not the curve component).
    add_option(list_name="data_source", fields={"value": "Bloomberg"}, actor="admin")
    for mid in ("M-AN", "M-UP"):
        add_model_item(model_id=mid, collection="data_sources",
                       fields={"data_source": "Bloomberg"}, actor="a")
    rebuild_inventory_view()
    register_product(product_id="P-1", product="Swap", actor="a",
                     fields={"calculating_agent": "Murex"})
    for mid, kind in [("M-AN", "Analytical Model"), ("M-CV", "Curve Model")]:
        add_product_item(product_id="P-1", collection=PRODUCT_COMPONENTS,
                         fields={"component_type": kind, "model_id": mid, "role": ""},
                         actor="a")
    rebuild_product_view()


def test_components_and_one_hop_feeds_are_in_the_map():
    _build()
    mp = derive_product_map("P-1")
    roles = {n["model_id"]: n["role"] for n in mp["nodes"]}
    # The two components plus M-UP, pulled in because it feeds a component.
    assert roles == {"M-AN": "component", "M-CV": "component", "M-UP": "feed"}
    assert mp["links"] == [{"from": "M-UP", "to": "M-AN"}]


def test_sources_are_nodes_linking_to_the_models_that_use_them():
    _build()
    mp = derive_product_map("P-1")
    by_name = {s["name"]: s for s in mp["sources"]}
    assert set(by_name) == {"Bloomberg"}
    assert by_name["Bloomberg"]["models"] == ["M-AN", "M-UP"]


def test_unknown_product_returns_none():
    assert derive_product_map("ghost") is None
