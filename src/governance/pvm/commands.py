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
"""Command handlers for the PVM aggregate (event-sourced, confirm-to-amend)."""
from __future__ import annotations

from typing import Any

from src.database import Event, append_event, read_stream
from src.governance.model_inventory import get_model
from src.governance.pvm._rules import (
    decide_add_item,
    decide_edit_field,
    decide_rebind,
    decide_register,
    decide_remove_item,
    decide_retire,
    decide_update_item,
)
from src.governance.pvm._state import PvmState, apply, initial_state

AGGREGATE_TYPE = "Pvm"

_COMBINATION_KEYS = ("product", "analytics_model", "market_data_model", "calculating_agent")


def _load(pvm_id: str, config) -> tuple[PvmState, int]:
    events = read_stream(aggregate_type=AGGREGATE_TYPE, aggregate_id=pvm_id, config=config)
    state = initial_state()
    for event in events:
        state = apply(state, event.event_type, event.payload)
    return state, len(events)


def _record(pvm_id, decision, version, actor, reason, config) -> Event:
    event_type, payload = decision
    return append_event(
        aggregate_type=AGGREGATE_TYPE, aggregate_id=pvm_id, event_type=event_type,
        payload=payload, actor=actor, reason=reason, expected_version=version, config=config)


def _analytics_live(model_id: str | None, config) -> bool:
    if not model_id:
        return False
    model = get_model(model_id, config=config)
    return bool(model and not model["retired"])


def _is_duplicate(combination: tuple, *, exclude_pvm_id: str, config) -> bool:
    """True if a non-retired PVM (other than this one) already binds this combo."""
    from src.governance.pvm.projection import list_pvms

    for pvm in list_pvms(config=config):
        if pvm["pvm_id"] == exclude_pvm_id or pvm["retired"]:
            continue
        if tuple(pvm["data"].get(key) for key in _COMBINATION_KEYS) == combination:
            return True
    return False


def register_pvm(
    *, pvm_id: str, product: str, fields: dict[str, Any] | None = None, actor: str,
    reason: str | None = None, config=None,
) -> Event:
    """Register a PVM binding a product to its three components."""
    state, version = _load(pvm_id, config)
    fields = dict(fields or {})
    analytics_live = _analytics_live(fields.get("analytics_model"), config)
    combination = (product,) + tuple(fields.get(k) for k in _COMBINATION_KEYS[1:])
    duplicate = _is_duplicate(combination, exclude_pvm_id=pvm_id, config=config)
    decision = decide_register(
        state, pvm_id=pvm_id, product=product, fields=fields,
        analytics_live=analytics_live, duplicate=duplicate)
    return _record(pvm_id, decision, version, actor, reason, config)


def rebind_component(
    *, pvm_id: str, component: str, value: str, actor: str,
    reason: str | None = None, config=None,
) -> Event:
    """Change one of a PVM's component bindings (Analytics / MDM / Agent)."""
    state, version = _load(pvm_id, config)
    analytics_live = _analytics_live(value, config) if component == "analytics_model" else True
    rebound = dict(state.fields)
    rebound[component] = value
    combination = tuple(rebound.get(key) for key in _COMBINATION_KEYS)
    duplicate = _is_duplicate(combination, exclude_pvm_id=pvm_id, config=config)
    decision = decide_rebind(
        state, component=component, value=value,
        analytics_live=analytics_live, duplicate=duplicate)
    return _record(pvm_id, decision, version, actor, reason, config)


def update_pvm_field(
    *, pvm_id: str, field: str, value: Any, actor: str,
    reason: str | None = None, config=None,
) -> Event:
    """Edit a scalar field of an existing PVM."""
    state, version = _load(pvm_id, config)
    decision = decide_edit_field(state, field=field, value=value)
    return _record(pvm_id, decision, version, actor, reason, config)


def retire_pvm(*, pvm_id: str, actor: str, reason: str | None = None, config=None) -> Event:
    """Retire a PVM (terminal; it can no longer be edited)."""
    state, version = _load(pvm_id, config)
    decision = decide_retire(state)
    return _record(pvm_id, decision, version, actor, reason, config)


def add_collection_item(
    *, pvm_id: str, collection: str, fields: dict[str, Any], actor: str,
    reason: str | None = None, config=None,
) -> Event:
    """Add a limitation or assumption to a PVM."""
    state, version = _load(pvm_id, config)
    decision = decide_add_item(state, collection=collection, fields=fields)
    return _record(pvm_id, decision, version, actor, reason, config)


def update_collection_item(
    *, pvm_id: str, collection: str, item_id: str, fields: dict[str, Any], actor: str,
    reason: str | None = None, config=None,
) -> Event:
    """Update a PVM limitation or assumption."""
    state, version = _load(pvm_id, config)
    decision = decide_update_item(state, collection=collection, item_id=item_id, fields=fields)
    return _record(pvm_id, decision, version, actor, reason, config)


def remove_collection_item(
    *, pvm_id: str, collection: str, item_id: str, actor: str,
    reason: str | None = None, config=None,
) -> Event:
    """Remove a PVM limitation or assumption."""
    state, version = _load(pvm_id, config)
    decision = decide_remove_item(state, collection=collection, item_id=item_id)
    return _record(pvm_id, decision, version, actor, reason, config)
