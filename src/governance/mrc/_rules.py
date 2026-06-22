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
"""Pure decision logic for the MRC-meeting aggregate."""
from __future__ import annotations

from typing import Any

from config.governance import (
    DEFAULT_ACTION_STATUS,
    DEFAULT_MEETING_STATUS,
    MEETING_FIELDS,
    VALID_ACTION_STATUSES,
    VALID_MEETING_STATUSES,
)
from src.governance.mrc._state import (
    EVENT_ACTION_RAISED,
    EVENT_ACTION_STATUS_SET,
    EVENT_AGENDA_ADDED,
    EVENT_DECISION_LOGGED,
    EVENT_FIELD_UPDATED,
    EVENT_SCHEDULED,
    MeetingState,
)


class DomainError(ValueError):
    """Raised when a command would violate a governance rule."""


def _require_exists(state: MeetingState) -> None:
    if not state.exists:
        raise DomainError("meeting does not exist")


def _next_id(prefix: str, count: int) -> str:
    return f"{prefix}-{count + 1:03d}"


def _validate_field(field: str, value: Any) -> None:
    if field == "status" and value not in VALID_MEETING_STATUSES:
        allowed = ", ".join(VALID_MEETING_STATUSES)
        raise DomainError(f"status must be one of: {allowed}")


def decide_schedule(
    state: MeetingState, *, meeting_id: str, title: str, date: str,
    fields: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    if state.exists:
        raise DomainError(f"meeting {meeting_id} is already scheduled")
    if not meeting_id or not title or not date:
        raise DomainError("meeting_id, title and date are required")
    for field, value in fields.items():
        if field not in MEETING_FIELDS:
            raise DomainError(f"unknown field: {field}")
        _validate_field(field, value)
    payload: dict[str, Any] = {
        "meeting_id": meeting_id,
        "title": title,
        "date": date,
        "status": DEFAULT_MEETING_STATUS,
    }
    payload.update(fields)
    return EVENT_SCHEDULED, payload


def decide_update_field(
    state: MeetingState, *, field: str, value: Any
) -> tuple[str, dict[str, Any]]:
    _require_exists(state)
    if field not in MEETING_FIELDS:
        raise DomainError(f"field not editable: {field}")
    _validate_field(field, value)
    return EVENT_FIELD_UPDATED, {"field": field, "value": value}


def decide_add_agenda_item(
    state: MeetingState, *, title: str, presenter: str | None = None
) -> tuple[str, dict[str, Any]]:
    _require_exists(state)
    if not title:
        raise DomainError("agenda item title is required")
    item_id = _next_id("AG", len(state.agenda))
    return EVENT_AGENDA_ADDED, {"item_id": item_id, "title": title, "presenter": presenter}


def decide_log_decision(
    state: MeetingState, *, text: str
) -> tuple[str, dict[str, Any]]:
    _require_exists(state)
    if not text:
        raise DomainError("decision text is required")
    decision_id = _next_id("D", len(state.decisions))
    return EVENT_DECISION_LOGGED, {"decision_id": decision_id, "text": text}


def decide_raise_action(
    state: MeetingState, *, description: str, owner: str, due_date: str | None = None
) -> tuple[str, dict[str, Any]]:
    _require_exists(state)
    if not description or not owner:
        raise DomainError("action description and owner are required")
    action_id = _next_id("A", len(state.actions))
    return EVENT_ACTION_RAISED, {
        "action_id": action_id,
        "description": description,
        "owner": owner,
        "due_date": due_date,
        "status": DEFAULT_ACTION_STATUS,
    }


def decide_set_action_status(
    state: MeetingState, *, action_id: str, status: str
) -> tuple[str, dict[str, Any]]:
    _require_exists(state)
    if status not in VALID_ACTION_STATUSES:
        allowed = ", ".join(VALID_ACTION_STATUSES)
        raise DomainError(f"status must be one of: {allowed}")
    if not any(action["action_id"] == action_id for action in state.actions):
        raise DomainError(f"unknown action: {action_id}")
    return EVENT_ACTION_STATUS_SET, {"action_id": action_id, "status": status}
