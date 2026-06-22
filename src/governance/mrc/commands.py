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
"""Command handlers for the MRC-meeting aggregate.

Each loads the meeting's event stream, rebuilds state, validates via the pure
decision functions, and appends the resulting event with optimistic
concurrency, recording the acting ``actor`` and change ``reason``.
"""
from __future__ import annotations

from typing import Any

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
        aggregate_type=AGGREGATE_TYPE,
        aggregate_id=meeting_id,
        event_type=event_type,
        payload=payload,
        actor=actor,
        reason=reason,
        expected_version=version,
        config=config,
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


def update_meeting_field(
    *, meeting_id: str, field: str, value: Any, actor: str,
    reason: str | None = None, config=None,
) -> Event:
    """Update a scalar field of a meeting (e.g. its status)."""
    state, version = _load(meeting_id, config)
    decision = _rules.decide_update_field(state, field=field, value=value)
    return _record(meeting_id, decision, version, actor, reason, config)


def add_agenda_item(
    *, meeting_id: str, title: str, actor: str, presenter: str | None = None,
    reason: str | None = None, config=None,
) -> Event:
    """Add an agenda item to a meeting."""
    state, version = _load(meeting_id, config)
    decision = _rules.decide_add_agenda_item(state, title=title, presenter=presenter)
    return _record(meeting_id, decision, version, actor, reason, config)


def log_decision(
    *, meeting_id: str, text: str, actor: str, reason: str | None = None, config=None,
) -> Event:
    """Record a decision taken at a meeting."""
    state, version = _load(meeting_id, config)
    decision = _rules.decide_log_decision(state, text=text)
    return _record(meeting_id, decision, version, actor, reason, config)


def raise_action(
    *, meeting_id: str, description: str, owner: str, actor: str,
    due_date: str | None = None, reason: str | None = None, config=None,
) -> Event:
    """Raise an action item from a meeting."""
    state, version = _load(meeting_id, config)
    decision = _rules.decide_raise_action(
        state, description=description, owner=owner, due_date=due_date
    )
    return _record(meeting_id, decision, version, actor, reason, config)


def set_action_status(
    *, meeting_id: str, action_id: str, status: str, actor: str,
    reason: str | None = None, config=None,
) -> Event:
    """Update the status of an existing action item."""
    state, version = _load(meeting_id, config)
    decision = _rules.decide_set_action_status(
        state, action_id=action_id, status=status
    )
    return _record(meeting_id, decision, version, actor, reason, config)
