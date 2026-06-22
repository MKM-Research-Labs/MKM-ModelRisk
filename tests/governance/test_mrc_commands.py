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
"""Tests for the MRC-meeting command handlers (against the event store)."""
from __future__ import annotations

import pytest

from src.database import read_stream
from src.governance.mrc import (
    AGGREGATE_TYPE,
    DomainError,
    add_agenda_item,
    log_decision,
    raise_action,
    schedule_meeting,
    set_action_status,
    update_meeting_field,
)


def test_schedule_appends_first_event():
    event = schedule_meeting(
        meeting_id="MTG1", title="Q2 MRC", date="2026-06-30", actor="alice"
    )
    assert event.stream_seq == 1
    assert event.event_type == "MeetingScheduled"
    assert event.actor == "alice"
    assert event.payload["status"] == "Scheduled"


def test_full_meeting_lifecycle_stream():
    schedule_meeting(meeting_id="MTG1", title="Q2 MRC", date="2026-06-30", actor="alice")
    update_meeting_field(
        meeting_id="MTG1", field="status", value="Held", actor="alice", reason="ran"
    )
    add_agenda_item(meeting_id="MTG1", title="Review tier-1 models", actor="alice")
    log_decision(meeting_id="MTG1", text="Approved recertification", actor="alice")
    raise_action(
        meeting_id="MTG1", description="Update inventory", owner="bob", actor="alice"
    )
    set_action_status(
        meeting_id="MTG1", action_id="A-001", status="Closed", actor="bob"
    )
    stream = read_stream(aggregate_type=AGGREGATE_TYPE, aggregate_id="MTG1")
    assert [e.event_type for e in stream] == [
        "MeetingScheduled",
        "MeetingFieldUpdated",
        "AgendaItemAdded",
        "DecisionLogged",
        "ActionRaised",
        "ActionStatusSet",
    ]


def test_schedule_duplicate_raises():
    schedule_meeting(meeting_id="MTG1", title="t", date="2026-06-30", actor="alice")
    with pytest.raises(DomainError):
        schedule_meeting(meeting_id="MTG1", title="t", date="2026-06-30", actor="alice")


def test_agenda_on_unknown_meeting_raises():
    with pytest.raises(DomainError):
        add_agenda_item(meeting_id="ghost", title="x", actor="alice")


def test_invalid_status_rejected_before_append():
    schedule_meeting(meeting_id="MTG1", title="t", date="2026-06-30", actor="alice")
    with pytest.raises(DomainError):
        update_meeting_field(
            meeting_id="MTG1", field="status", value="Bogus", actor="alice"
        )
    assert len(read_stream(aggregate_type=AGGREGATE_TYPE, aggregate_id="MTG1")) == 1
