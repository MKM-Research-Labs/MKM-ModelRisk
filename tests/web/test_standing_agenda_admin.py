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
"""A committee's running order is its own.

The shipped agenda — rollcall, the previous minutes, the sign-off review, the
analysis review, the completeness audit, AOB — is where a committee starts, not
what it is stuck with. It is an admin list, copied onto each meeting when it is
scheduled, so a meeting always shows the agenda it was actually given and editing
the list never rewrites a meeting already held.
"""
from __future__ import annotations

from config.governance import STANDING_AGENDA, STANDING_AGENDA_LIST
from src.governance.reference import (ensure_default_standing_agenda,
                                      get_reference_lists)
from tests.web._signoff_flows import _schedule_meeting, _seed_mrc
from tests.web.conftest import HEADERS


def _agenda(client, meeting_id="MTG1"):
    return client.get(f"/api/meetings/{meeting_id}").get_json()["data"]["agenda"]


def _add_item(client, title, description="", kind=""):
    """A blank role is omitted, not sent as "": a choice field holds one of its
    options or nothing at all, and the console omits empty values the same way."""
    fields = {"title": title, "description": description}
    if kind:
        fields["kind"] = kind
    return client.post(f"/api/reference/collections/{STANDING_AGENDA_LIST}",
                       json={"fields": fields, "confirmed": True}, headers=HEADERS)


def test_the_shipped_order_seeds_a_vacuum_only():
    assert ensure_default_standing_agenda() == len(STANDING_AGENDA)
    assert ensure_default_standing_agenda() == 0
    seeded = get_reference_lists()[STANDING_AGENDA_LIST]
    assert [i["title"] for i in seeded] == [i["title"] for i in STANDING_AGENDA]


def test_a_meeting_is_seeded_with_the_committees_own_agenda(client):
    _seed_mrc(client)
    _add_item(client, "Attendance", "Confirm quorum.", kind="rollcall")
    _add_item(client, "Regulatory horizon", "What is coming, and who owns it.")
    _schedule_meeting(client)
    items = _agenda(client)
    assert [i["title"] for i in items] == ["Attendance", "Regulatory horizon"]
    # An item with no role is ordinary business, which is what it is.
    assert items[0]["kind"] == "rollcall" and not items[1].get("kind")


def test_editing_the_agenda_does_not_touch_a_meeting_already_held(client):
    _seed_mrc(client)
    _add_item(client, "Attendance", kind="rollcall")
    _schedule_meeting(client)
    listed = get_reference_lists()[STANDING_AGENDA_LIST]
    client.post(f"/api/reference/collections/{STANDING_AGENDA_LIST}/{listed[0]['item_id']}",
                json={"fields": {"title": "Rollcall and quorum"}, "confirmed": True},
                headers=HEADERS)

    assert [i["title"] for i in _agenda(client)] == ["Attendance"]
    _schedule_meeting(client, meeting_id="MTG2", date="2026-12-15")
    assert [i["title"] for i in _agenda(client, "MTG2")] == ["Rollcall and quorum"]


def test_an_empty_list_still_gives_a_meeting_the_shipped_order(client):
    """A meeting with no agenda at all would be worse than one with the defaults."""
    _seed_mrc(client)
    assert not get_reference_lists()[STANDING_AGENDA_LIST]
    _schedule_meeting(client)
    assert len(_agenda(client)) == len(STANDING_AGENDA)


def test_reordering_changes_what_the_next_meeting_takes_first(client):
    _seed_mrc(client)
    _add_item(client, "First", kind="rollcall")
    _add_item(client, "Second")
    listed = get_reference_lists()[STANDING_AGENDA_LIST]
    client.post(f"/api/reference/collections/{STANDING_AGENDA_LIST}/{listed[1]['item_id']}/move",
                json={"direction": "up", "confirmed": True}, headers=HEADERS)
    _schedule_meeting(client)
    assert [i["title"] for i in _agenda(client)] == ["Second", "First"]


def test_editing_the_agenda_needs_confirmation(client):
    """A committee's running order is a standard, not working vocabulary."""
    unconfirmed = client.post(f"/api/reference/collections/{STANDING_AGENDA_LIST}",
                              json={"fields": {"title": "Slipped in quietly"}},
                              headers=HEADERS)
    assert unconfirmed.status_code == 409
    assert not get_reference_lists()[STANDING_AGENDA_LIST]
