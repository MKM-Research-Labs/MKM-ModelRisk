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
"""Tests for the Product aggregate (domain core)."""
from __future__ import annotations

import pytest

from config.governance import PRODUCT_COMPONENTS

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

_BINDINGS = {"calculating_agent": "Murex"}


def _component(product_id="Product-0001", model_id="MKM-AN-001",
               component_type="Analytical Model", role=""):
    """Bind a model to a Product as a component, the way the detail view does."""
    add_collection_item(product_id=product_id, collection=PRODUCT_COMPONENTS,
                        fields={"component_type": component_type,
                                "model_id": model_id, "role": role},
                        actor="admin")
    rebuild_product_view()


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
    # No components yet, so nothing to derive an identifier from.
    assert product["data"]["identifier"] is None
    _component()
    assert get_product("Product-0001")["data"]["identifier"] == "MKM-AN-001.Murex"


def test_registration_seeds_the_four_raci_accountabilities():
    """A product's RACI operating model is scaffolded at registration: one entry
    per accountability, with a standard governance role the owner then edits."""
    _register()
    raci = get_product("Product-0001")["data"]["raci_roles"]
    assert [r["raci"] for r in raci] == ["Responsible", "Accountable", "Consulted", "Informed"]
    assert [r["role"] for r in raci] == [
        "Model user", "Model owner", "Model Risk Committee", "Senior management"]
    assert [r["item_id"] for r in raci] == ["RC-001", "RC-002", "RC-003", "RC-004"]


def test_first_component_gives_the_product_its_org_home():
    # A product's division / line of business follow its first component, so it
    # lands under the right MRC region instead of unscoped (and hidden from the
    # list). Components arrive after registration, so the default lands with them.
    register_model(model_id="MKM-AN-001", name="Analytics engine", actor="admin",
                   fields={"division": "ANALYTICS", "line_of_business": "Asset Management"})
    rebuild_inventory_view()
    _register()
    _component()
    data = get_product("Product-0001")["data"]
    assert data["division"] == "ANALYTICS"
    assert data["line_of_business"] == "Asset Management"


def test_explicit_org_survives_the_first_component():
    register_model(model_id="MKM-AN-001", name="Analytics engine", actor="admin",
                   fields={"division": "ANALYTICS", "line_of_business": "Asset Management"})
    rebuild_inventory_view()
    _register(division="RATINGS")
    _component()
    data = get_product("Product-0001")["data"]
    # An explicit division wins; line_of_business still falls back to the model's.
    assert data["division"] == "RATINGS"
    assert data["line_of_business"] == "Asset Management"


def test_register_requires_the_calculating_agent():
    """The one binding that is not a model. Components are added afterwards, so
    they are deliberately not required here."""
    _live_model()
    with pytest.raises(DomainError):
        register_product(product_id="Product-X", product="Bond", actor="admin",
                         fields={})


def test_register_requires_product():
    _live_model()
    with pytest.raises(DomainError):
        register_product(product_id="Product-X", product="", actor="admin", fields=dict(_BINDINGS))


def test_register_rejects_unknown_field():
    _live_model()
    with pytest.raises(DomainError):
        register_product(product_id="Product-X", product="Bond", actor="admin",
                     fields={**_BINDINGS, "bogus": "x"})


def test_same_name_is_allowed_until_the_components_match():
    """Two Products may share a name while they are built out differently —
    that is the variant case. They only collide once they bind the same models."""
    _live_model()
    _live_model("MKM-AN-002")
    _register(product_id="Product-0001")
    _component(product_id="Product-0001", model_id="MKM-AN-001")
    _register(product_id="Product-0002")
    _component(product_id="Product-0002", model_id="MKM-AN-002")
    assert get_product("Product-0002")["data"]["identifier"] == "MKM-AN-002.Murex"


def test_duplicate_component_set_rejected():
    _live_model()
    _register(product_id="Product-0001")
    _component(product_id="Product-0001", model_id="MKM-AN-001")
    _register(product_id="Product-0002")
    with pytest.raises(DomainError):
        _component(product_id="Product-0002", model_id="MKM-AN-001")


def test_retired_product_components_can_be_reused():
    _live_model()
    _register(product_id="Product-0001")
    _component(product_id="Product-0001", model_id="MKM-AN-001")
    retire_product(product_id="Product-0001", actor="admin")
    rebuild_product_view()
    _register(product_id="Product-0002")
    _component(product_id="Product-0002", model_id="MKM-AN-001")
    assert get_product("Product-0002") is not None


def test_register_duplicate_id_rejected():
    _live_model()
    _register(product_id="Product-0001")
    with pytest.raises(DomainError):
        register_product(product_id="Product-0001", product="Other", actor="admin",
                     fields={**_BINDINGS})


def test_rebind_changes_identifier():
    _live_model()
    _register()
    _component()
    rebind_component(product_id="Product-0001", component="calculating_agent", value="Calypso", actor="admin")
    rebuild_product_view()
    assert get_product("Product-0001")["data"]["identifier"] == "MKM-AN-001.Calypso"


def test_components_can_be_swapped_and_the_identifier_follows():
    _live_model("MKM-AN-001")
    _live_model("MKM-AN-002")
    _register()
    _component(model_id="MKM-AN-001")
    item = get_product("Product-0001")["data"][PRODUCT_COMPONENTS][0]
    update_collection_item(product_id="Product-0001", collection=PRODUCT_COMPONENTS,
                           item_id=item["item_id"], fields={"model_id": "MKM-AN-002"},
                           actor="admin")
    rebuild_product_view()
    assert get_product("Product-0001")["data"]["identifier"] == "MKM-AN-002.Murex"


def test_rebind_unknown_component_rejected():
    _live_model()
    _register()
    with pytest.raises(DomainError):
        rebind_component(product_id="Product-0001", component="analytics_model", value="NOPE", actor="admin")


def test_rebind_unknown_component_rejected():
    _live_model()
    _register()
    with pytest.raises(DomainError):
        rebind_component(product_id="Product-0001", component="owner", value="x", actor="admin")


def test_several_components_of_one_type_are_allowed():
    """Structured products combine several models of the same kind — two curve
    models is the ordinary case, not an error."""
    _live_model("MKM-CV-001")
    _live_model("MKM-CV-002")
    _register()
    _component(model_id="MKM-CV-001", component_type="Curve Model", role="Hazard")
    _component(model_id="MKM-CV-002", component_type="Curve Model", role="Recovery")
    data = get_product("Product-0001")["data"]
    assert len(data[PRODUCT_COMPONENTS]) == 2
    assert data["identifier"] == "MKM-CV-001.MKM-CV-002.Murex"


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
    built = {"calculating_agent": "G",
             PRODUCT_COMPONENTS: [{"model_id": "M"}, {"model_id": "A"}]}
    # Sorted, so the identifier says what the Product is rather than the order
    # its components happened to be added in.
    assert derived_identifier(built) == "A.M.G"
    assert derived_identifier({"calculating_agent": "G"}) is None
    assert derived_identifier({PRODUCT_COMPONENTS: [{"model_id": "A"}]}) is None


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
