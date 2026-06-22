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
"""Unit tests for the pure MRC-meeting decision logic and state fold."""
from __future__ import annotations

import pytest

from src.governance.mrc._rules import (
    DomainError,
    decide_add_agenda_item,
    decide_log_decision,
    decide_raise_action,
    decide_schedule,
    decide_set_action_status,
    decide_update_field,
)
from src.governance.mrc._state import (
    EVENT_ACTION_RAISED,
    EVENT_ACTION_STATUS_SET,
    EVENT_AGENDA_ADDED,
    EVENT_DECISION_LOGGED,
    EVENT_SCHEDULED,
    apply,
    initial_state,
)


def _scheduled():
    event_type, payload = decide_schedule(
        initial_state(), meeting_id="MTG1", title="Q2 MRC", date="2026-06-30", fields={}
    )
    return apply(initial_state(), event_type, payload)


def test_schedule_sets_default_status():
    event_type, payload = decide_schedule(
        initial_state(), meeting_id="MTG1", title="Q2 MRC", date="2026-06-30", fields={}
    )
    assert event_type == EVENT_SCHEDULED
    assert payload["status"] == "Scheduled"
    assert payload["title"] == "Q2 MRC"


def test_schedule_rejects_duplicate():
    with pytest.raises(DomainError):
        decide_schedule(
            _scheduled(), meeting_id="MTG1", title="x", date="2026-06-30", fields={}
        )


@pytest.mark.parametrize(
    "meeting_id,title,date",
    [("", "t", "d"), ("M", "", "d"), ("M", "t", "")],
)
def test_schedule_requires_core_fields(meeting_id, title, date):
    with pytest.raises(DomainError):
        decide_schedule(
            initial_state(), meeting_id=meeting_id, title=title, date=date, fields={}
        )


def test_schedule_rejects_unknown_field():
    with pytest.raises(DomainError):
        decide_schedule(
            initial_state(), meeting_id="M", title="t", date="d",
            fields={"bogus": 1},
        )


def test_schedule_with_valid_status_field():
    _, payload = decide_schedule(
        initial_state(), meeting_id="M", title="t", date="d",
        fields={"status": "Held", "location": "Room 1"},
    )
    assert payload["status"] == "Held"
    assert payload["location"] == "Room 1"


def test_schedule_rejects_invalid_status_field():
    with pytest.raises(DomainError):
        decide_schedule(
            initial_state(), meeting_id="M", title="t", date="d",
            fields={"status": "Bogus"},
        )


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


def test_agenda_items_get_sequential_ids():
    state = _scheduled()
    _, first = decide_add_agenda_item(state, title="Opening")
    assert first["item_id"] == "AG-001"
    state = apply(state, EVENT_AGENDA_ADDED, first)
    _, second = decide_add_agenda_item(state, title="Review", presenter="Alice")
    assert second["item_id"] == "AG-002"
    assert second["presenter"] == "Alice"


def test_agenda_requires_title_and_meeting():
    with pytest.raises(DomainError):
        decide_add_agenda_item(_scheduled(), title="")
    with pytest.raises(DomainError):
        decide_add_agenda_item(initial_state(), title="x")


def test_decision_gets_sequential_id():
    _, payload = decide_log_decision(_scheduled(), text="Approved tier 2")
    assert payload["decision_id"] == "D-001"


def test_decision_requires_text_and_meeting():
    with pytest.raises(DomainError):
        decide_log_decision(_scheduled(), text="")
    with pytest.raises(DomainError):
        decide_log_decision(initial_state(), text="x")


def test_action_gets_id_and_default_status():
    _, payload = decide_raise_action(_scheduled(), description="Do X", owner="bob")
    assert payload["action_id"] == "A-001"
    assert payload["status"] == "Open"


def test_action_requires_description_owner_and_meeting():
    with pytest.raises(DomainError):
        decide_raise_action(_scheduled(), description="", owner="bob")
    with pytest.raises(DomainError):
        decide_raise_action(_scheduled(), description="x", owner="")
    with pytest.raises(DomainError):
        decide_raise_action(initial_state(), description="x", owner="bob")


def _with_action():
    state = _scheduled()
    _, action = decide_raise_action(state, description="Do X", owner="bob")
    return apply(state, EVENT_ACTION_RAISED, action)


def test_set_action_status_ok():
    _, payload = decide_set_action_status(_with_action(), action_id="A-001", status="Closed")
    assert payload == {"action_id": "A-001", "status": "Closed"}


def test_set_action_status_requires_meeting():
    with pytest.raises(DomainError):
        decide_set_action_status(initial_state(), action_id="A-001", status="Closed")


def test_set_action_status_rejects_invalid_status():
    with pytest.raises(DomainError):
        decide_set_action_status(_with_action(), action_id="A-001", status="Bogus")


def test_set_action_status_rejects_unknown_action():
    with pytest.raises(DomainError):
        decide_set_action_status(_with_action(), action_id="A-999", status="Closed")


def test_apply_ignores_unknown_event():
    state = _scheduled()
    assert apply(state, "Whatever", {}) == state


def test_apply_action_status_only_touches_matching_action():
    state = _scheduled()
    _, a1 = decide_raise_action(state, description="X", owner="bob")
    state = apply(state, EVENT_ACTION_RAISED, a1)
    _, a2 = decide_raise_action(state, description="Y", owner="carol")
    state = apply(state, EVENT_ACTION_RAISED, a2)
    state = apply(state, EVENT_ACTION_STATUS_SET, {"action_id": "A-002", "status": "Closed"})
    statuses = {a["action_id"]: a["status"] for a in state.actions}
    assert statuses == {"A-001": "Open", "A-002": "Closed"}


def test_apply_decision_appends():
    state = apply(_scheduled(), EVENT_DECISION_LOGGED, {"decision_id": "D-001", "text": "ok"})
    assert state.decisions[0]["text"] == "ok"
