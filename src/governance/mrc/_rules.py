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
"""Pure decision logic for the MRC-meeting aggregate."""
from __future__ import annotations

from typing import Any

from config.governance import (
    CLOSED_MEETING_STATUS,
    DEFAULT_MEETING_STATUS,
    MEETING_FIELDS,
    MRC_COLLECTION_SPECS,
    VALID_MEETING_STATUSES,
)
from src.governance import collections as coll
from src.governance.errors import DomainError
from src.governance.mrc._state import EVENT_FIELD_UPDATED, EVENT_SCHEDULED, MeetingState


def _require_exists(state: MeetingState) -> None:
    if not state.exists:
        raise DomainError("meeting does not exist")


def _require_open(state: MeetingState) -> None:
    """A closed meeting is a finished record, not a working document.

    Once the chair closes a meeting its minutes are generated and filed, so
    editing it afterwards would change what the committee is recorded as having
    decided. A correction is raised and minuted at the next meeting instead —
    which is how a committee actually works, and leaves the trail intact. Enforced
    here rather than in the console so it holds for the API too."""
    if state.fields.get("status") == CLOSED_MEETING_STATUS:
        raise DomainError(
            "meeting is closed and cannot be amended; raise the correction at the "
            "next meeting")


def _validate_field(field: str, value: Any) -> None:
    if field == "status" and value not in VALID_MEETING_STATUSES:
        allowed = ", ".join(VALID_MEETING_STATUSES)
        raise DomainError(f"status must be one of: {allowed}")


def decide_schedule(
    state: MeetingState, *, meeting_id: str, title: str, date: str, fields: dict[str, Any]
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
        "meeting_id": meeting_id, "title": title, "date": date,
        "status": DEFAULT_MEETING_STATUS,
    }
    payload.update(fields)
    return EVENT_SCHEDULED, payload


def decide_update_field(
    state: MeetingState, *, field: str, value: Any
) -> tuple[str, dict[str, Any]]:
    _require_exists(state)
    _require_open(state)
    if field not in MEETING_FIELDS:
        raise DomainError(f"field not editable: {field}")
    _validate_field(field, value)
    return EVENT_FIELD_UPDATED, {"field": field, "value": value}


def decide_add_item(
    state: MeetingState, *, collection: str, fields: dict[str, Any]
) -> tuple[str, dict[str, Any]]:
    _require_exists(state)
    _require_open(state)
    return coll.decide_add(
        state.collections, MRC_COLLECTION_SPECS, collection=collection, fields=fields
    )


def decide_update_item(
    state: MeetingState, *, collection: str, item_id: str, fields: dict[str, Any]
) -> tuple[str, dict[str, Any]]:
    _require_exists(state)
    _require_open(state)
    return coll.decide_update(
        state.collections, MRC_COLLECTION_SPECS,
        collection=collection, item_id=item_id, fields=fields,
    )


def decide_remove_item(
    state: MeetingState, *, collection: str, item_id: str
) -> tuple[str, dict[str, Any]]:
    _require_exists(state)
    _require_open(state)
    return coll.decide_remove(
        state.collections, MRC_COLLECTION_SPECS, collection=collection, item_id=item_id
    )
