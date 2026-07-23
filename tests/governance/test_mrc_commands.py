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
"""Tests for the MRC-meeting command handlers (against the event store)."""
from __future__ import annotations

import pytest

from src.database import read_stream
from src.governance.mrc import (
    AGGREGATE_TYPE,
    DomainError,
    add_collection_item,
    remove_collection_item,
    schedule_meeting,
    update_collection_item,
    update_meeting_field,
)


def test_schedule_appends_first_event():
    event = schedule_meeting(meeting_id="MTG1", title="Q2 MRC", date="2026-06-30", actor="a")
    assert event.stream_seq == 1
    assert event.event_type == "MeetingScheduled"
    assert event.payload["status"] == "Scheduled"


def test_full_meeting_lifecycle_stream():
    schedule_meeting(meeting_id="MTG1", title="Q2 MRC", date="2026-06-30", actor="a")
    # Not "Completed": closing a meeting seals it, so the work below would be
    # refused. Closing is exercised in test_meeting_is_sealed_once_closed.
    update_meeting_field(meeting_id="MTG1", field="location", value="Room A", actor="a")
    add_collection_item(meeting_id="MTG1", collection="agenda", fields={"title": "Review"}, actor="a")
    add_collection_item(meeting_id="MTG1", collection="actions",
                        fields={"description": "Follow up", "owner": "bob"}, actor="a")
    update_collection_item(meeting_id="MTG1", collection="actions", item_id="A-001",
                           fields={"status": "Closed"}, actor="bob")
    remove_collection_item(meeting_id="MTG1", collection="agenda", item_id="AG-001", actor="a")
    types = [e.event_type for e in read_stream(aggregate_type=AGGREGATE_TYPE, aggregate_id="MTG1")]
    assert types == [
        "MeetingScheduled", "MeetingFieldUpdated", "CollectionItemAdded",
        "CollectionItemAdded", "CollectionItemUpdated", "CollectionItemRemoved",
    ]


def test_schedule_duplicate_raises():
    schedule_meeting(meeting_id="MTG1", title="t", date="2026-06-30", actor="a")
    with pytest.raises(DomainError):
        schedule_meeting(meeting_id="MTG1", title="t", date="2026-06-30", actor="a")


def test_add_item_on_unknown_meeting_raises():
    with pytest.raises(DomainError):
        add_collection_item(meeting_id="ghost", collection="agenda",
                            fields={"title": "x"}, actor="a")


def test_meeting_is_sealed_once_closed():
    """A closed meeting is a finished record: its minutes are filed and what the
    committee decided cannot be quietly restated. Corrections go to the next
    meeting, which is how a committee works and keeps the trail intact."""
    schedule_meeting(meeting_id="MTG2", title="Q3 MRC", date="2026-09-30", actor="a")
    update_meeting_field(meeting_id="MTG2", field="status", value="Completed", actor="a")
    for call in (
        lambda: update_meeting_field(meeting_id="MTG2", field="location",
                                     value="Elsewhere", actor="a"),
        lambda: add_collection_item(meeting_id="MTG2", collection="agenda",
                                    fields={"title": "Late item"}, actor="a"),
        lambda: update_collection_item(meeting_id="MTG2", collection="agenda",
                                       item_id="AG-001", fields={"title": "X"}, actor="a"),
        lambda: remove_collection_item(meeting_id="MTG2", collection="agenda",
                                       item_id="AG-001", actor="a"),
    ):
        with pytest.raises(DomainError, match="closed"):
            call()
