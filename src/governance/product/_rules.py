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
"""Pure decision logic for the Product aggregate (validation only, no I/O).

Cross-aggregate facts (does the Analytics Model resolve to a live model; would
the component combination duplicate an existing Product) are computed by the command
layer and passed in, so these functions stay pure and unit-testable.
"""
from __future__ import annotations

from typing import Any

from config.governance import (
    COMPONENT_KIND_MODEL,
    FUNCTIONAL_GROUP_FIELD,
    PRODUCT_BINDINGS,
    PRODUCT_COMPONENTS,
    VALID_COMPONENT_KINDS,
    component_kind,
    PRODUCT_COLLECTION_SPECS,
    PRODUCT_EDITABLE_FIELDS,
    PRODUCT_FIELD_CHOICES,
    PRODUCT_FIELD_SPECS,
    SIGNOFF_COLLECTIONS,
)
from src.governance import collections as coll
from src.governance.errors import DomainError
from src.governance.product._state import (
    EVENT_FIELD_EDITED,
    EVENT_REBOUND,
    EVENT_REACTIVATED,
    EVENT_REGISTERED,
    EVENT_RETIRED,
    ProductState,
)
from src.governance.functional_groups import (reject_division_move_while_grouped,
                                              reject_unknown_functional_group)
from src.governance.risk_policy import get_risk_policy

# Risk fields whose allowed values come from the product's DIVISION policy.
_POLICY_CHOICE_FIELDS = {
    "materiality": lambda policy: [b["name"] for b in policy["dimensions"]["materiality"]["bands"]],
    "complexity": lambda policy: [b["name"] for b in policy["dimensions"]["complexity"]["bands"]],
    "rag_rating": lambda policy: [b["name"] for b in policy["risk_ratings"]],
}


def _validate_field(field: str, value: Any, division: Any) -> None:
    if field in _POLICY_CHOICE_FIELDS:
        allowed = _POLICY_CHOICE_FIELDS[field](get_risk_policy(division or ""))
        if value not in allowed:
            raise DomainError(f"{field} must be one of: {', '.join(allowed)}")
    elif field == FUNCTIONAL_GROUP_FIELD:
        reject_unknown_functional_group(value, division)
    elif field in PRODUCT_FIELD_CHOICES and value not in PRODUCT_FIELD_CHOICES[field]:
        allowed = ", ".join(PRODUCT_FIELD_CHOICES[field])
        raise DomainError(f"{field} must be one of: {allowed}")


def _require_editable(state: ProductState) -> None:
    if not state.exists:
        raise DomainError("Product does not exist")
    if state.retired:
        raise DomainError("cannot edit a retired Product")


def decide_register(
    state: ProductState, *, product_id: str, product: str, fields: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    """Register a Product.

    Model components are not required here and duplicates are not checked here:
    a Product's identity is its name plus the set of models it binds, and that set
    is empty until components are added. Checking at registration would reject two
    same-named Products before either had the components that distinguish them —
    the variants this design exists to allow. The duplicate rule is enforced where
    the set actually changes; see ``decide_add_item``.
    """
    if state.exists:
        raise DomainError(f"Product {product_id} is already registered")
    if not product_id or not product:
        raise DomainError("product_id and product are required")
    for binding in PRODUCT_BINDINGS:
        if not fields.get(binding):
            raise DomainError(f"{binding} is required")
    division = fields.get("division")
    for field, value in fields.items():
        if field not in PRODUCT_FIELD_SPECS:
            raise DomainError(f"unknown field: {field}")
        _validate_field(field, value, division)
    payload: dict[str, Any] = {"product_id": product_id, "product": product, "status": "Proposed"}
    payload.update(fields)
    return EVENT_REGISTERED, payload


def decide_rebind(
    state: ProductState, *, component: str, value: str,
) -> tuple[str, dict[str, Any]]:
    """Change the Calculating Agent — the one binding that is not a model."""
    _require_editable(state)
    if component not in PRODUCT_BINDINGS:
        raise DomainError(f"not a component binding: {component}")
    if not value:
        raise DomainError(f"{component} is required")
    return EVENT_REBOUND, {"component": component, "value": value}


def decide_edit_field(
    state: ProductState, *, field: str, value: Any
) -> tuple[str, dict[str, Any]]:
    _require_editable(state)
    if field not in PRODUCT_EDITABLE_FIELDS:
        raise DomainError(f"field not editable: {field}")
    division = value if field == "division" else state.fields.get("division")
    if field == "division":
        reject_division_move_while_grouped(state.fields, value)
    _validate_field(field, value, division)
    return EVENT_FIELD_EDITED, {"field": field, "value": value}


def decide_retire(state: ProductState) -> tuple[str, dict[str, Any]]:
    """Hibernate a Product. Ratified by the MRC, so this runs off an approved
    request rather than straight from the owner.

    Carries the status it is about to overwrite, so a later reactivation can put
    it back. A Product retired before this recorded it simply has none, which
    ``decide_reactivate`` handles rather than guessing.
    """
    if not state.exists:
        raise DomainError("Product does not exist")
    if state.retired:
        raise DomainError("Product is already retired")
    payload: dict[str, Any] = {}
    current = state.fields.get("status")
    if current and current != "Retired":
        payload["from_status"] = current
    return EVENT_RETIRED, payload


def decide_reactivate(state: ProductState) -> tuple[str, dict[str, Any]]:
    """Bring a hibernated Product back. Ratified by the MRC on the same footing
    as the retire that put it there.

    Restores the status the retire displaced. Where the retire recorded none the
    status stays "Retired" on a live Product -- wrong, but visible, and editable
    again the moment the record is back. The alternative is picking a status out
    of the vocabulary on the committee's behalf, which is the sort of invention an
    audit trail exists to prevent.
    """
    if not state.exists:
        raise DomainError("Product does not exist")
    if not state.retired:
        raise DomainError("Product is not retired")
    return EVENT_REACTIVATED, ({"status": state.status_before_retire}
                               if state.status_before_retire else {})


def _validate_component(fields: dict[str, Any]) -> None:
    """A component row must say what it is, and a model component must say its type.

    The type comes from the admin model_type list and describes a model's part in the
    product. An ML Application has no entry there -- its provenance is its Estimator --
    so requiring one would force whoever binds it to pick a lie from a dropdown.
    """
    kind = component_kind(fields)
    if kind not in VALID_COMPONENT_KINDS:
        raise DomainError(f"kind must be one of: {', '.join(VALID_COMPONENT_KINDS)}")
    if kind == COMPONENT_KIND_MODEL and not fields.get("component_type"):
        raise DomainError("component_type is required for a model component")


def _require_signoff_writable(state: ProductState, collection: str) -> None:
    """A hibernated Product is read-only, except to the committee's own machinery.

    Reactivating it has to be requested *on* it, and the decision that hibernated it
    still has to be recordable against it -- so the sign-off queue and history stay
    writable while everything else is frozen. Every subject in the routing carries
    this exemption; without it the committee cannot complete the request it just
    approved.
    """
    if collection in SIGNOFF_COLLECTIONS:
        if not state.exists:
            raise DomainError("Product does not exist")
        return
    _require_editable(state)


def decide_add_item(
    state: ProductState, *, collection: str, fields: dict[str, Any],
    duplicate: bool = False,
) -> tuple[str, dict[str, Any]]:
    """Add a collection item.

    ``duplicate`` is only ever true for the components collection: adding this
    component would leave the Product with the same name and the same set of
    models as another live Product, which is what makes two Products the same
    thing registered twice. The command computes it (it needs the other Products);
    the rule only decides what to do about it.
    """
    _require_signoff_writable(state, collection)
    if collection == PRODUCT_COMPONENTS:
        _validate_component(fields)
    if duplicate:
        raise DomainError(
            "another Product of this name already binds exactly these components")
    return coll.decide_add(
        state.collections, PRODUCT_COLLECTION_SPECS, collection=collection, fields=fields)


def decide_update_item(
    state: ProductState, *, collection: str, item_id: str, fields: dict[str, Any]
) -> tuple[str, dict[str, Any]]:
    _require_signoff_writable(state, collection)
    return coll.decide_update(
        state.collections, PRODUCT_COLLECTION_SPECS, collection=collection, item_id=item_id, fields=fields)


def decide_remove_item(
    state: ProductState, *, collection: str, item_id: str
) -> tuple[str, dict[str, Any]]:
    _require_editable(state)
    return coll.decide_remove(
        state.collections, PRODUCT_COLLECTION_SPECS, collection=collection, item_id=item_id)
