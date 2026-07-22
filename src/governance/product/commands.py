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

from src.database import Event, append_event, read_stream
from src.governance.model_inventory import get_model
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

_COMBINATION_KEYS = ("product", "analytics_model", "market_data_model", "calculating_agent")


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


def _analytics_live(model_id: str | None, config) -> bool:
    if not model_id:
        return False
    model = get_model(model_id, config=config)
    return bool(model and not model["retired"])


def _is_duplicate(combination: tuple, *, exclude_product_id: str, config) -> bool:
    """True if a non-retired Product (other than this one) already binds this combo."""
    from src.governance.product.projection import list_products

    for product in list_products(config=config):
        if product["product_id"] == exclude_product_id or product["retired"]:
            continue
        if tuple(product["data"].get(key) for key in _COMBINATION_KEYS) == combination:
            return True
    return False


def _default_org_from_analytics(fields: dict[str, Any], config) -> None:
    """A product's org home (division / line of business) follows its analytics model
    unless explicitly given, so it lands under the right division / line of business —
    and thus the right MRC — rather than unscoped and hidden from the region view."""
    model = get_model(fields.get("analytics_model"), config=config) if fields.get("analytics_model") else None
    data = (model or {}).get("data") or {}
    for key in ("division", "line_of_business"):
        if not fields.get(key) and data.get(key):
            fields[key] = data[key]


def register_product(
    *, product_id: str, product: str, fields: dict[str, Any] | None = None, actor: str,
    reason: str | None = None, config=None,
) -> Event:
    """Register a Product binding a product to its three components."""
    state, version = _load(product_id, config)
    fields = dict(fields or {})
    _default_org_from_analytics(fields, config)
    analytics_live = _analytics_live(fields.get("analytics_model"), config)
    combination = (product,) + tuple(fields.get(k) for k in _COMBINATION_KEYS[1:])
    duplicate = _is_duplicate(combination, exclude_product_id=product_id, config=config)
    decision = decide_register(
        state, product_id=product_id, product=product, fields=fields,
        analytics_live=analytics_live, duplicate=duplicate)
    return _record(product_id, decision, version, actor, reason, config)


def rebind_component(
    *, product_id: str, component: str, value: str, actor: str,
    reason: str | None = None, config=None,
) -> Event:
    """Change one of a Product's component bindings (Analytics / MDM / Agent)."""
    state, version = _load(product_id, config)
    analytics_live = _analytics_live(value, config) if component == "analytics_model" else True
    rebound = dict(state.fields)
    rebound[component] = value
    combination = tuple(rebound.get(key) for key in _COMBINATION_KEYS)
    duplicate = _is_duplicate(combination, exclude_product_id=product_id, config=config)
    decision = decide_rebind(
        state, component=component, value=value,
        analytics_live=analytics_live, duplicate=duplicate)
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
    """Add a limitation or assumption to a Product."""
    state, version = _load(product_id, config)
    decision = decide_add_item(state, collection=collection, fields=fields)
    return _record(product_id, decision, version, actor, reason, config)


def update_collection_item(
    *, product_id: str, collection: str, item_id: str, fields: dict[str, Any], actor: str,
    reason: str | None = None, config=None,
) -> Event:
    """Update a Product limitation or assumption."""
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
