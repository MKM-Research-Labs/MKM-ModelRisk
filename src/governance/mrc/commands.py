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
"""Command handlers for the MRC-meeting aggregate."""
from __future__ import annotations

from typing import Any

from config.governance import STANDING_AGENDA
from src.database import Event, append_event, read_stream
from src.governance.mrc import _rules
from src.governance.mrc._state import MeetingState, apply, initial_state

AGGREGATE_TYPE = "MRCMeeting"


def _load(meeting_id: str, config) -> tuple[MeetingState, int]:
    events = read_stream(
        aggregate_type=AGGREGATE_TYPE, aggregate_id=meeting_id, config=config
    )
    state = initial_state()
    for event in events:
        state = apply(state, event.event_type, event.payload)
    return state, len(events)


def _record(
    meeting_id: str, decision: tuple[str, dict[str, Any]], version: int,
    actor: str, reason: str | None, config,
) -> Event:
    event_type, payload = decision
    return append_event(
        aggregate_type=AGGREGATE_TYPE, aggregate_id=meeting_id,
        event_type=event_type, payload=payload, actor=actor, reason=reason,
        expected_version=version, config=config,
    )


def schedule_meeting(
    *, meeting_id: str, title: str, date: str, actor: str,
    fields: dict[str, Any] | None = None, reason: str | None = None, config=None,
) -> Event:
    """Schedule a new MRC meeting."""
    state, version = _load(meeting_id, config)
    decision = _rules.decide_schedule(
        state, meeting_id=meeting_id, title=title, date=date, fields=fields or {}
    )
    return _record(meeting_id, decision, version, actor, reason, config)


def seed_standing_agenda(
    *, meeting_id: str, actor: str, reason: str | None = None, config=None,
) -> list[Event]:
    """Seed the standing agenda (rollcall … AOB) onto a freshly-scheduled meeting.

    Shared by every creation path — the web ``schedule`` endpoint and the demo
    seeder — so the standing items are never missed. ``schedule_meeting`` stays a
    single-event command; the standing items are ordinary ``CollectionItemAdded``
    events layered on afterwards.
    """
    return [
        add_collection_item(
            meeting_id=meeting_id, collection="agenda", fields=dict(item),
            actor=actor, reason=reason, config=config,
        )
        for item in STANDING_AGENDA
    ]


def update_meeting_field(
    *, meeting_id: str, field: str, value: Any, actor: str,
    reason: str | None = None, config=None,
) -> Event:
    """Update a scalar field of a meeting (e.g. its status)."""
    state, version = _load(meeting_id, config)
    decision = _rules.decide_update_field(state, field=field, value=value)
    return _record(meeting_id, decision, version, actor, reason, config)


def add_collection_item(
    *, meeting_id: str, collection: str, fields: dict[str, Any], actor: str,
    reason: str | None = None, config=None,
) -> Event:
    """Add an item to a meeting collection (agenda, decisions, actions, …)."""
    state, version = _load(meeting_id, config)
    decision = _rules.decide_add_item(state, collection=collection, fields=fields)
    return _record(meeting_id, decision, version, actor, reason, config)


def update_collection_item(
    *, meeting_id: str, collection: str, item_id: str, fields: dict[str, Any],
    actor: str, reason: str | None = None, config=None,
) -> Event:
    """Update fields of an existing meeting collection item."""
    state, version = _load(meeting_id, config)
    decision = _rules.decide_update_item(
        state, collection=collection, item_id=item_id, fields=fields
    )
    return _record(meeting_id, decision, version, actor, reason, config)


def remove_collection_item(
    *, meeting_id: str, collection: str, item_id: str, actor: str,
    reason: str | None = None, config=None,
) -> Event:
    """Remove an item from a meeting collection."""
    state, version = _load(meeting_id, config)
    decision = _rules.decide_remove_item(state, collection=collection, item_id=item_id)
    return _record(meeting_id, decision, version, actor, reason, config)
