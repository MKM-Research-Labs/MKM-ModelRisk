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
"""Unit tests for the pure MRC-meeting decision logic and state fold."""
from __future__ import annotations

import pytest

from src.governance.mrc._rules import (
    DomainError,
    decide_add_item,
    decide_remove_item,
    decide_schedule,
    decide_update_field,
    decide_update_item,
)
from src.governance.mrc._state import EVENT_SCHEDULED, apply, initial_state


def _scheduled():
    return apply(initial_state(), EVENT_SCHEDULED, {
        "meeting_id": "M1", "title": "Q2 MRC", "date": "2026-06-30", "status": "Scheduled",
    })


def _add(state, collection, fields):
    event_type, payload = decide_add_item(state, collection=collection, fields=fields)
    return apply(state, event_type, payload), payload


def test_schedule_sets_default_status():
    event_type, payload = decide_schedule(
        initial_state(), meeting_id="M1", title="Q2", date="2026-06-30", fields={}
    )
    assert event_type == EVENT_SCHEDULED
    assert payload["status"] == "Scheduled"


def test_schedule_rejects_duplicate():
    with pytest.raises(DomainError):
        decide_schedule(_scheduled(), meeting_id="M1", title="x", date="d", fields={})


@pytest.mark.parametrize("mid,title,date", [("", "t", "d"), ("M", "", "d"), ("M", "t", "")])
def test_schedule_requires_core_fields(mid, title, date):
    with pytest.raises(DomainError):
        decide_schedule(initial_state(), meeting_id=mid, title=title, date=date, fields={})


def test_schedule_rejects_unknown_field():
    with pytest.raises(DomainError):
        decide_schedule(initial_state(), meeting_id="M", title="t", date="d", fields={"x": 1})


def test_schedule_with_valid_status_field():
    _, payload = decide_schedule(
        initial_state(), meeting_id="M", title="t", date="d",
        fields={"status": "Completed", "location": "Room 1"},
    )
    assert payload["status"] == "Completed" and payload["location"] == "Room 1"


def test_schedule_rejects_invalid_status():
    with pytest.raises(DomainError):
        decide_schedule(initial_state(), meeting_id="M", title="t", date="d",
                        fields={"status": "Bogus"})


def test_update_field_requires_meeting():
    with pytest.raises(DomainError):
        decide_update_field(initial_state(), field="location", value="Room 2")


def test_update_field_rejects_unknown_field():
    with pytest.raises(DomainError):
        decide_update_field(_scheduled(), field="bogus", value="x")


def test_update_field_validates_status():
    with pytest.raises(DomainError):
        decide_update_field(_scheduled(), field="status", value="Bogus")


def test_update_free_text_field_ok():
    _, payload = decide_update_field(_scheduled(), field="location", value="Room 2")
    assert payload == {"field": "location", "value": "Room 2"}


def test_add_agenda_item_generates_id():
    state, payload = _add(_scheduled(), "agenda", {"title": "Opening", "presenter": "Alice"})
    assert payload["item_id"] == "AG-001"
    assert state.collections["agenda"][0]["presenter"] == "Alice"


def test_add_participant_item():
    _, payload = decide_add_item(
        _scheduled(), collection="participants",
        fields={"name": "Bob", "status": "Attended"},
    )
    assert payload["item_id"] == "P-001"


def test_add_requires_meeting():
    with pytest.raises(DomainError):
        decide_add_item(initial_state(), collection="agenda", fields={"title": "x"})


def test_add_unknown_collection():
    with pytest.raises(DomainError):
        decide_add_item(_scheduled(), collection="nope", fields={"title": "x"})


def test_add_missing_required():
    with pytest.raises(DomainError):
        decide_add_item(_scheduled(), collection="agenda", fields={"presenter": "Alice"})


def test_update_item_changes_status():
    state, _ = _add(_scheduled(), "actions", {"description": "Do X", "owner": "bob"})
    event_type, payload = decide_update_item(
        state, collection="actions", item_id="A-001", fields={"status": "Closed"}
    )
    state = apply(state, event_type, payload)
    assert state.collections["actions"][0]["status"] == "Closed"


def test_update_item_requires_meeting():
    with pytest.raises(DomainError):
        decide_update_item(initial_state(), collection="actions", item_id="A-001", fields={})


def test_remove_item():
    state, _ = _add(_scheduled(), "decisions", {"description": "Approved"})
    event_type, payload = decide_remove_item(state, collection="decisions", item_id="D-001")
    state = apply(state, event_type, payload)
    assert state.collections["decisions"] == ()


def test_remove_item_requires_meeting():
    with pytest.raises(DomainError):
        decide_remove_item(initial_state(), collection="decisions", item_id="D-001")


def test_apply_ignores_unknown_event():
    state = _scheduled()
    assert apply(state, "Whatever", {}) == state
