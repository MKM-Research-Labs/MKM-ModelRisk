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
"""Command handlers for the Client aggregate (event-sourced, confirm-to-amend)."""
from __future__ import annotations

from typing import Any

from config.governance import CLIENT_ID_PREFIX, CLIENT_PACKS
from src.database import Event, append_event, read_all, read_stream
from src.governance.client._rules import (
    decide_add_item,
    decide_edit_field,
    decide_register,
    decide_remove_item,
    decide_retire,
    decide_update_item,
)
from src.governance.client._state import (
    EVENT_REGISTERED,
    ClientState,
    apply,
    initial_state,
)

AGGREGATE_TYPE = "Client"


def _load(client_id: str, config) -> tuple[ClientState, int]:
    events = read_stream(aggregate_type=AGGREGATE_TYPE, aggregate_id=client_id, config=config)
    state = initial_state()
    for event in events:
        state = apply(state, event.event_type, event.payload)
    return state, len(events)


def _record(client_id, decision, version, actor, reason, config) -> Event:
    event_type, payload = decision
    return append_event(
        aggregate_type=AGGREGATE_TYPE, aggregate_id=client_id, event_type=event_type,
        payload=payload, actor=actor, reason=reason, expected_version=version, config=config)


def _next_client_id(config) -> str:
    """The next ``CL-NNN`` id, counted from the event log rather than the view.

    Reading the log (not ``client_view``) means the id is correct even before the
    projection is rebuilt — two registrations in one request never collide on a
    stale count. This is a single-institution console, so the count is small and a
    full scan is cheap; a concurrent double-register would collide on the derived
    stream id and fail cleanly as "already registered" rather than double-book.
    """
    registered = {
        event.aggregate_id for event in read_all(config=config)
        if event.aggregate_type == AGGREGATE_TYPE and event.event_type == EVENT_REGISTERED
    }
    return f"{CLIENT_ID_PREFIX}-{len(registered) + 1:03d}"


def register_client(
    *, name: str, fields: dict[str, Any] | None = None, actor: str,
    reason: str | None = None, config=None,
) -> Event:
    """Register a Client company. The id (CL-NNN) is generated server-side."""
    client_id = _next_client_id(config)
    state, version = _load(client_id, config)
    decision = decide_register(
        state, client_id=client_id, name=name, fields=dict(fields or {}))
    return _record(client_id, decision, version, actor, reason, config)


def update_client_field(
    *, client_id: str, field: str, value: Any, actor: str,
    reason: str | None = None, config=None,
) -> Event:
    """Edit a scalar field of an existing Client."""
    state, version = _load(client_id, config)
    decision = decide_edit_field(state, field=field, value=value)
    return _record(client_id, decision, version, actor, reason, config)


def retire_client(*, client_id: str, actor: str, reason: str | None = None, config=None) -> Event:
    """Retire a Client (terminal; it can no longer be edited)."""
    state, version = _load(client_id, config)
    decision = decide_retire(state)
    return _record(client_id, decision, version, actor, reason, config)


def add_collection_item(
    *, client_id: str, collection: str, fields: dict[str, Any], actor: str,
    reason: str | None = None, config=None,
) -> Event:
    """Add a division, department, contact or link to a Client."""
    state, version = _load(client_id, config)
    decision = decide_add_item(state, collection=collection, fields=fields)
    return _record(client_id, decision, version, actor, reason, config)


def update_collection_item(
    *, client_id: str, collection: str, item_id: str, fields: dict[str, Any], actor: str,
    reason: str | None = None, config=None,
) -> Event:
    """Update a Client division, department, contact or link."""
    state, version = _load(client_id, config)
    decision = decide_update_item(state, collection=collection, item_id=item_id, fields=fields)
    return _record(client_id, decision, version, actor, reason, config)


def remove_collection_item(
    *, client_id: str, collection: str, item_id: str, actor: str,
    reason: str | None = None, config=None,
) -> Event:
    """Remove a Client division, department, contact or link."""
    state, version = _load(client_id, config)
    decision = decide_remove_item(state, collection=collection, item_id=item_id)
    return _record(client_id, decision, version, actor, reason, config)


def record_client_pack(
    *, client_id: str, as_of: str, generated_at: str, filename: str,
    original_name: str, size: int, actor: str, reason: str | None = None, config=None,
) -> Event:
    """Append one generated pack to the client's bi-temporal pack history.

    Server-stamps both times: ``as_of`` (valid time — the governance state the pack
    reflects) and ``generated_at`` (transaction time — when it was produced). The
    fields are set here rather than accepted from the request so a history row can
    never disagree with the file that was actually stored.
    """
    state, version = _load(client_id, config)
    fields = {
        "as_of": as_of, "generated_at": generated_at, "filename": filename,
        "original_name": original_name, "size": size,
    }
    decision = decide_add_item(state, collection=CLIENT_PACKS, fields=fields)
    return _record(client_id, decision, version, actor, reason, config)
