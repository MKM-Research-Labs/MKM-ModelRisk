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
"""Tests for the MRC-meeting read-model projection."""
from __future__ import annotations

from src.database import append_event
from src.governance.mrc import (
    add_agenda_item,
    get_meeting,
    list_meetings,
    log_decision,
    raise_action,
    rebuild_meeting_view,
    schedule_meeting,
    set_action_status,
    update_meeting_field,
)


def _populate(meeting_id="MTG1"):
    schedule_meeting(meeting_id=meeting_id, title="Q2 MRC", date="2026-06-30", actor="a")
    add_agenda_item(meeting_id=meeting_id, title="Review", actor="a", presenter="bob")
    log_decision(meeting_id=meeting_id, text="Approved", actor="a")
    raise_action(meeting_id=meeting_id, description="Follow up", owner="bob", actor="a")


def test_rebuild_reflects_meeting_and_collections():
    _populate()
    update_meeting_field(meeting_id="MTG1", field="status", value="Held", actor="a")
    set_action_status(meeting_id="MTG1", action_id="A-001", status="Closed", actor="a")
    assert rebuild_meeting_view() == 1

    meeting = get_meeting("MTG1")
    assert meeting["meeting_id"] == "MTG1"
    assert meeting["status"] == "Held"
    assert meeting["data"]["title"] == "Q2 MRC"
    assert meeting["data"]["agenda"][0]["item_id"] == "AG-001"
    assert meeting["data"]["decisions"][0]["text"] == "Approved"
    assert meeting["data"]["actions"][0]["status"] == "Closed"


def test_list_meetings_is_ordered():
    schedule_meeting(meeting_id="MTG2", title="B", date="2026-07-01", actor="a")
    schedule_meeting(meeting_id="MTG1", title="A", date="2026-06-30", actor="a")
    rebuild_meeting_view()
    assert [m["meeting_id"] for m in list_meetings()] == ["MTG1", "MTG2"]


def test_get_meeting_returns_none_when_absent():
    rebuild_meeting_view()
    assert get_meeting("missing") is None


def test_rebuild_ignores_other_aggregate_types():
    _populate()
    append_event(
        aggregate_type="SomethingElse", aggregate_id="X",
        event_type="Noted", payload={}, actor="system",
    )
    assert rebuild_meeting_view() == 1
    assert [m["meeting_id"] for m in list_meetings()] == ["MTG1"]
