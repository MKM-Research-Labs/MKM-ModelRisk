# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Tests for the Product aggregate (domain core)."""
from __future__ import annotations

import pytest

from src.governance.errors import DomainError
from src.governance.model_inventory import rebuild_inventory_view, register_model, retire_model
from src.governance.product import (
    add_collection_item,
    derived_identifier,
    get_product,
    list_products,
    rebind_component,
    rebuild_product_view,
    register_product,
    remove_collection_item,
    retire_product,
    update_collection_item,
    update_product_field,
)

_BINDINGS = {"analytics_model": "MKM-AN-001", "market_data_model": "MDM-001", "calculating_agent": "Murex"}


def _live_model(model_id="MKM-AN-001"):
    register_model(model_id=model_id, name="Analytics engine", actor="admin")
    rebuild_inventory_view()
    return model_id


def _register(product_id="Product-0001", product="Government Bond", **overrides):
    fields = {**_BINDINGS, **overrides}
    register_product(product_id=product_id, product=product, actor="admin", fields=fields)
    rebuild_product_view()


def test_register_and_derived_identifier():
    _live_model()
    _register()
    product = get_product("Product-0001")
    assert product["data"]["product"] == "Government Bond"
    assert product["data"]["status"] == "Proposed"
    assert product["data"]["identifier"] == "MKM-AN-001.MDM-001.Murex"


def test_register_inherits_org_from_analytics_model():
    # A product's division/department follow its analytics model, so it lands
    # under the right MRC region instead of unscoped (and hidden from the list).
    register_model(model_id="MKM-AN-001", name="Analytics engine", actor="admin",
                   fields={"division": "ANALYTICS", "department": "Asset Management"})
    rebuild_inventory_view()
    _register()
    data = get_product("Product-0001")["data"]
    assert data["division"] == "ANALYTICS"
    assert data["department"] == "Asset Management"


def test_register_org_can_be_overridden_explicitly():
    register_model(model_id="MKM-AN-001", name="Analytics engine", actor="admin",
                   fields={"division": "ANALYTICS", "department": "Asset Management"})
    rebuild_inventory_view()
    _register(division="RATINGS")
    data = get_product("Product-0001")["data"]
    # An explicit division wins; department still falls back to the model's.
    assert data["division"] == "RATINGS"
    assert data["department"] == "Asset Management"


def test_register_requires_each_binding():
    _live_model()
    with pytest.raises(DomainError):
        register_product(product_id="Product-X", product="Bond", actor="admin",
                     fields={"analytics_model": "MKM-AN-001", "market_data_model": "MDM-001"})


def test_register_requires_product():
    _live_model()
    with pytest.raises(DomainError):
        register_product(product_id="Product-X", product="", actor="admin", fields=dict(_BINDINGS))


def test_register_rejects_unknown_field():
    _live_model()
    with pytest.raises(DomainError):
        register_product(product_id="Product-X", product="Bond", actor="admin",
                     fields={**_BINDINGS, "bogus": "x"})


def test_analytics_must_resolve_to_live_model():
    with pytest.raises(DomainError):
        register_product(product_id="Product-X", product="Bond", actor="admin",
                     fields={**_BINDINGS, "analytics_model": "DOES-NOT-EXIST"})


def test_analytics_retired_model_rejected():
    _live_model()
    retire_model(model_id="MKM-AN-001", actor="admin")
    rebuild_inventory_view()
    with pytest.raises(DomainError):
        register_product(product_id="Product-X", product="Bond", actor="admin", fields=dict(_BINDINGS))


def test_duplicate_combination_rejected():
    _live_model()
    _register(product_id="Product-0001")
    with pytest.raises(DomainError):
        register_product(product_id="Product-0002", product="Government Bond", actor="admin", fields=dict(_BINDINGS))


def test_retired_product_combination_can_be_reused():
    _live_model()
    _register(product_id="Product-0001")
    retire_product(product_id="Product-0001", actor="admin")
    rebuild_product_view()
    register_product(product_id="Product-0002", product="Government Bond", actor="admin", fields=dict(_BINDINGS))
    rebuild_product_view()
    assert get_product("Product-0002") is not None


def test_register_duplicate_id_rejected():
    _live_model()
    _register(product_id="Product-0001")
    with pytest.raises(DomainError):
        register_product(product_id="Product-0001", product="Other", actor="admin",
                     fields={**_BINDINGS, "market_data_model": "MDM-002"})


def test_rebind_changes_identifier():
    _live_model()
    _register()
    rebind_component(product_id="Product-0001", component="calculating_agent", value="Calypso", actor="admin")
    rebuild_product_view()
    assert get_product("Product-0001")["data"]["identifier"] == "MKM-AN-001.MDM-001.Calypso"


def test_rebind_analytics_to_another_live_model():
    _live_model("MKM-AN-001")
    _live_model("MKM-AN-002")
    _register()
    rebind_component(product_id="Product-0001", component="analytics_model", value="MKM-AN-002", actor="admin")
    rebuild_product_view()
    assert get_product("Product-0001")["data"]["analytics_model"] == "MKM-AN-002"


def test_rebind_analytics_to_dead_model_rejected():
    _live_model()
    _register()
    with pytest.raises(DomainError):
        rebind_component(product_id="Product-0001", component="analytics_model", value="NOPE", actor="admin")


def test_rebind_unknown_component_rejected():
    _live_model()
    _register()
    with pytest.raises(DomainError):
        rebind_component(product_id="Product-0001", component="owner", value="x", actor="admin")


def test_rebind_duplicate_rejected():
    _live_model()
    _register(product_id="Product-0001", calculating_agent="Murex")
    _register(product_id="Product-0002", calculating_agent="Calypso")
    with pytest.raises(DomainError):
        rebind_component(product_id="Product-0002", component="calculating_agent", value="Murex", actor="admin")


def test_edit_field_and_monitoring():
    _live_model()
    _register()
    update_product_field(product_id="Product-0001", field="status", value="Active", actor="admin")
    update_product_field(product_id="Product-0001", field="monitoring_approach", value="P&L backtest", actor="admin")
    rebuild_product_view()
    data = get_product("Product-0001")["data"]
    assert data["status"] == "Active" and data["monitoring_approach"] == "P&L backtest"


def test_edit_field_rejects_binding_and_bad_status():
    _live_model()
    _register()
    with pytest.raises(DomainError):
        update_product_field(product_id="Product-0001", field="analytics_model", value="X", actor="admin")
    with pytest.raises(DomainError):
        update_product_field(product_id="Product-0001", field="status", value="Bogus", actor="admin")


def test_retire_makes_read_only():
    _live_model()
    _register()
    retire_product(product_id="Product-0001", actor="admin")
    rebuild_product_view()
    product = get_product("Product-0001")
    assert product["retired"] and product["data"]["status"] == "Retired"
    with pytest.raises(DomainError):
        update_product_field(product_id="Product-0001", field="notes", value="x", actor="admin")
    with pytest.raises(DomainError):
        retire_product(product_id="Product-0001", actor="admin")


def test_retire_unknown_product_rejected():
    with pytest.raises(DomainError):
        retire_product(product_id="Product-NONE", actor="admin")


def test_limitations_and_assumptions():
    _live_model()
    _register()
    add_collection_item(product_id="Product-0001", collection="limitations",
                        fields={"description": "Misses barrier risk", "impact": "High"}, actor="admin")
    update_collection_item(product_id="Product-0001", collection="limitations", item_id="LM-001",
                           fields={"impact": "Medium"}, actor="admin")
    rebuild_product_view()
    lim = get_product("Product-0001")["data"]["limitations"][0]
    assert lim["item_id"] == "LM-001" and lim["impact"] == "Medium"
    remove_collection_item(product_id="Product-0001", collection="limitations", item_id="LM-001", actor="admin")
    rebuild_product_view()
    assert get_product("Product-0001")["data"].get("limitations", []) == []


def test_get_unknown_is_none_and_list():
    assert get_product("Product-NONE") is None
    _live_model()
    _register()
    assert [p["product_id"] for p in list_products()] == ["Product-0001"]


def test_derived_identifier_helper():
    assert derived_identifier(
        {"analytics_model": "A", "market_data_model": "M", "calculating_agent": "G"}) == "A.M.G"
    assert derived_identifier({"analytics_model": "A"}) is None


def test_register_without_analytics_rejected():
    with pytest.raises(DomainError):
        register_product(product_id="Product-X", product="Bond", actor="admin",
                     fields={"market_data_model": "MDM-001", "calculating_agent": "Murex"})


def test_edit_or_rebind_unknown_product_rejected():
    with pytest.raises(DomainError):
        update_product_field(product_id="Product-NONE", field="notes", value="x", actor="admin")
    with pytest.raises(DomainError):
        rebind_component(product_id="Product-NONE", component="calculating_agent", value="X", actor="admin")


def test_rebind_requires_value():
    _live_model()
    _register()
    with pytest.raises(DomainError):
        rebind_component(product_id="Product-0001", component="calculating_agent", value="", actor="admin")


def test_projection_ignores_unrelated_event():
    from src.database import append_event

    _live_model()
    _register()
    append_event(aggregate_type="Product", aggregate_id="Product-0001",
                 event_type="Noise", payload={}, actor="system")
    rebuild_product_view()
    assert get_product("Product-0001")["data"]["product"] == "Government Bond"
