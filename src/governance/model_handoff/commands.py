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
"""Command handlers for the model-handoff aggregate.

A handoff is keyed by the directed edge it sits on (``from~to``). Declaring one is
only allowed on an edge that actually exists in the derived chain — that
cross-aggregate check reads the inventory, so it lives here rather than in the
pure rules. Everything else follows the standard load -> decide -> record shape.
"""
from __future__ import annotations

from typing import Any

from src.database import Event, append_event, read_stream
from src.governance.errors import DomainError
from src.governance.model_handoff._rules import (
    decide_add_item,
    decide_declare,
    decide_remove_item,
    decide_update_field,
    decide_update_item,
)
from src.governance.model_handoff._state import HandoffState, apply, initial_state
from src.governance.model_inventory import get_model
from src.governance.model_inventory.chain import all_edges

AGGREGATE_TYPE = "ModelHandoff"
SEPARATOR = "~"


def handoff_id(from_model: str, to_model: str) -> str:
    """The deterministic id for the handoff on a given edge (one per edge)."""
    return f"{from_model}{SEPARATOR}{to_model}"


def split_handoff_id(hid: str) -> tuple[str, str]:
    from_model, _, to_model = hid.partition(SEPARATOR)
    return from_model, to_model


def _load(hid: str, config) -> tuple[HandoffState, int]:
    events = read_stream(aggregate_type=AGGREGATE_TYPE, aggregate_id=hid, config=config)
    state = initial_state()
    for event in events:
        state = apply(state, event.event_type, event.payload)
    return state, len(events)


def _record(hid, decision, version, actor, reason, config) -> Event:
    event_type, payload = decision
    return append_event(
        aggregate_type=AGGREGATE_TYPE, aggregate_id=hid, event_type=event_type,
        payload=payload, actor=actor, reason=reason, expected_version=version, config=config,
    )


def _require_edge(from_model: str, to_model: str, config) -> None:
    """A handoff may only be declared on an edge that exists in the chain."""
    if get_model(from_model, config=config) is None:
        raise DomainError(f"unknown model: {from_model}")
    if get_model(to_model, config=config) is None:
        raise DomainError(f"unknown model: {to_model}")
    if (from_model, to_model) not in all_edges(config=config):
        raise DomainError(
            f"no declared dependency from {from_model} to {to_model} — "
            "declare the edge on the producing model first"
        )


def declare_handoff(
    *, from_model: str, to_model: str, actor: str, reason: str | None = None, config=None,
) -> Event:
    """Declare the handoff on a chain edge (idempotent per edge — one handoff)."""
    _require_edge(from_model, to_model, config)
    hid = handoff_id(from_model, to_model)
    state, version = _load(hid, config)
    decision = decide_declare(state, from_model=from_model, to_model=to_model)
    return _record(hid, decision, version, actor, reason, config)


def update_handoff_field(
    *, handoff_id: str, field: str, value: Any, actor: str,
    reason: str | None = None, config=None,
) -> Event:
    state, version = _load(handoff_id, config)
    decision = decide_update_field(state, field=field, value=value)
    return _record(handoff_id, decision, version, actor, reason, config)


def add_collection_item(
    *, handoff_id: str, collection: str, fields: dict[str, Any], actor: str,
    reason: str | None = None, config=None,
) -> Event:
    state, version = _load(handoff_id, config)
    decision = decide_add_item(state, collection=collection, fields=fields)
    return _record(handoff_id, decision, version, actor, reason, config)


def update_collection_item(
    *, handoff_id: str, collection: str, item_id: str, fields: dict[str, Any],
    actor: str, reason: str | None = None, config=None,
) -> Event:
    state, version = _load(handoff_id, config)
    decision = decide_update_item(state, collection=collection, item_id=item_id, fields=fields)
    return _record(handoff_id, decision, version, actor, reason, config)


def remove_collection_item(
    *, handoff_id: str, collection: str, item_id: str, actor: str,
    reason: str | None = None, config=None,
) -> Event:
    state, version = _load(handoff_id, config)
    decision = decide_remove_item(state, collection=collection, item_id=item_id)
    return _record(handoff_id, decision, version, actor, reason, config)
