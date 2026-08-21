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
"""Command handlers for the Product aggregate (event-sourced, confirm-to-amend)."""
from __future__ import annotations

from typing import Any

from config.governance import (DEFAULT_RACI, PRODUCT_COLLECTION_SPECS,
                               PRODUCT_COMPONENTS, component_kind)
from src.governance import collections as coll
from src.governance.errors import DomainError
from src.governance.reference import reject_unknown_values
from src.governance.seeding import seed_items
from src.database import Event, append_event, read_stream
from src.governance.product._rules import (
    decide_add_item,
    decide_edit_field,
    decide_rebind,
    decide_register,
    decide_remove_item,
    decide_retire,
    decide_update_item,
)
from src.governance.product._state import ProductState, apply, initial_state

AGGREGATE_TYPE = "Product"

def _component_set(data: dict[str, Any]) -> frozenset:
    """A Product's components as an order-independent set of (type, model) pairs.

    Order carries no meaning — a Product built from a hazard curve and a pricing
    engine is the same Product whichever was added first — so identity compares
    sets, not lists.
    """
    return frozenset(
        (component_kind(item), str(item.get("component_type") or ""),
         str(item.get("model_id") or ""))
        for item in (data.get(PRODUCT_COMPONENTS) or []) if isinstance(item, dict))


def _load(product_id: str, config) -> tuple[ProductState, int]:
    events = read_stream(aggregate_type=AGGREGATE_TYPE, aggregate_id=product_id, config=config)
    state = initial_state()
    for event in events:
        state = apply(state, event.event_type, event.payload)
    return state, len(events)


def _record(product_id, decision, version, actor, reason, config) -> Event:
    event_type, payload = decision
    return append_event(
        aggregate_type=AGGREGATE_TYPE, aggregate_id=product_id, event_type=event_type,
        payload=payload, actor=actor, reason=reason, expected_version=version, config=config)


def _is_duplicate(name: str, components: frozenset, *, exclude_product_id: str,
                  config) -> bool:
    """True if another live Product has this name and exactly these components.

    An empty component set never collides: a Product registered but not yet built
    out is not a duplicate of every other unbuilt Product of the same name.
    """
    from src.governance.product.projection import list_products

    if not components:
        return False
    for product in list_products(config=config):
        if product["product_id"] == exclude_product_id or product["retired"]:
            continue
        data = product["data"] or {}
        if data.get("product") == name and _component_set(data) == components:
            return True
    return False


def _seed_raci(product_id, after_version, actor, config) -> None:
    """Scaffold the four RACI accountabilities immediately after registration.

    A product's RACI operating model is complete only with all of Responsible /
    Accountable / Consulted / Informed, so registration seeds one entry per code
    (each with a standard governance role the owner edits) — the same way a model's
    nine SR 26-2 validation questions are seeded on registration.
    """
    seed_items(aggregate_type=AGGREGATE_TYPE, aggregate_id=product_id,
               collection="raci_roles", id_prefix="RC",
               items=[{"role": role, "raci": raci} for raci, role in DEFAULT_RACI],
               after_version=after_version, actor=actor,
               reason="Seed the four RACI accountabilities", config=config)


def register_product(
    *, product_id: str, product: str, fields: dict[str, Any] | None = None, actor: str,
    reason: str | None = None, config=None,
) -> Event:
    """Register a Product binding a product to its three components, then seed its
    four RACI accountabilities."""
    state, version = _load(product_id, config)
    decision = decide_register(
        state, product_id=product_id, product=product, fields=dict(fields or {}))
    event = _record(product_id, decision, version, actor, reason, config)
    _seed_raci(product_id, event.stream_seq, actor, config)
    return event


def rebind_component(
    *, product_id: str, component: str, value: str, actor: str,
    reason: str | None = None, config=None,
) -> Event:
    """Change one of a Product's component bindings (Analytics / MDM / Agent)."""
    state, version = _load(product_id, config)
    decision = decide_rebind(state, component=component, value=value)
    return _record(product_id, decision, version, actor, reason, config)


def update_product_field(
    *, product_id: str, field: str, value: Any, actor: str,
    reason: str | None = None, config=None,
) -> Event:
    """Edit a scalar field of an existing Product."""
    state, version = _load(product_id, config)
    decision = decide_edit_field(state, field=field, value=value)
    return _record(product_id, decision, version, actor, reason, config)


def retire_product(*, product_id: str, actor: str, reason: str | None = None, config=None) -> Event:
    """Retire a Product (terminal; it can no longer be edited)."""
    state, version = _load(product_id, config)
    decision = decide_retire(state)
    return _record(product_id, decision, version, actor, reason, config)


def add_collection_item(
    *, product_id: str, collection: str, fields: dict[str, Any], actor: str,
    reason: str | None = None, config=None,
) -> Event:
    """Add a component, limitation or assumption to a Product."""
    reject_unknown_values(PRODUCT_COLLECTION_SPECS, collection, fields, config)
    state, version = _load(product_id, config)
    duplicate = False
    first_component = False
    if collection == PRODUCT_COMPONENTS:
        first_component = not state.collections.get(PRODUCT_COMPONENTS)
        after = _component_set({PRODUCT_COMPONENTS:
                                list(state.collections.get(PRODUCT_COMPONENTS, ())) + [fields]})
        duplicate = _is_duplicate(state.fields.get("product"), after,
                                  exclude_product_id=product_id, config=config)
    decision = decide_add_item(state, collection=collection, fields=fields,
                               duplicate=duplicate)
    event = _record(product_id, decision, version, actor, reason, config)
    if first_component:
        _inherit_org_from(product_id, fields.get("model_id"), actor, config)
    return event


def _inherit_org_from(product_id: str, model_id, actor: str, config) -> None:
    """Give a Product the org home of its first component, where it has none.

    A Product's division and Line of Business decide which MRC owns it, so one
    left unscoped is hidden from the committee that should be reviewing it. This
    used to happen at registration, from the analytics model; components arrive
    after registration now, so the first one carries the default instead.

    Only fills what is blank — an explicitly-set division is never overwritten —
    and never fails the component add: the component is the thing being recorded,
    and a default that could not be applied is not a reason to lose it.
    """
    from src.governance.model_inventory import get_model

    if not model_id:
        return
    source = ((get_model(model_id, config=config) or {}).get("data") or {})
    for field in ("division", "line_of_business"):
        state, version = _load(product_id, config)
        if state.fields.get(field) or not source.get(field):
            continue
        try:
            decision = decide_edit_field(state, field=field, value=source[field])
            _record(product_id, decision, version, actor,
                    "Org inherited from first component", config)
        except DomainError:
            return


def update_collection_item(
    *, product_id: str, collection: str, item_id: str, fields: dict[str, Any], actor: str,
    reason: str | None = None, config=None,
) -> Event:
    """Update a Product limitation or assumption."""
    reject_unknown_values(PRODUCT_COLLECTION_SPECS, collection, fields, config)
    state, version = _load(product_id, config)
    decision = decide_update_item(state, collection=collection, item_id=item_id, fields=fields)
    return _record(product_id, decision, version, actor, reason, config)


def remove_collection_item(
    *, product_id: str, collection: str, item_id: str, actor: str,
    reason: str | None = None, config=None,
) -> Event:
    """Remove a Product limitation or assumption."""
    state, version = _load(product_id, config)
    decision = decide_remove_item(state, collection=collection, item_id=item_id)
    return _record(product_id, decision, version, actor, reason, config)
