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
"""A role is granted by a committee, not by whoever edits the screen (permissions P2).

Admin proposes; the MRC ratifies at its "Committee membership and roles" agenda item.
Until then the proposal has no effect on what the system believes a person may be.
"""
from __future__ import annotations

from src.identity import roles_for
from tests.web.conftest import HEADERS

PEOPLE = "/api/reference/collections/people"


def _person(client, name, pending=None):
    fields = {"name": name}
    if pending is not None:
        fields["pending_roles"] = pending
    client.post(PEOPLE, json={"fields": fields, "confirmed": True}, headers=HEADERS)
    listed = client.get("/api/reference").get_json()["data"]["people"]
    return next(p for p in listed if p["name"] == name)


def _meeting(client, meeting_id="MTG-MEM"):
    client.post("/api/meetings", json={"meeting_id": meeting_id, "title": "Q1",
                                       "date": "2026-09-01", "confirmed": True},
                headers=HEADERS)
    return meeting_id


def test_the_standing_agenda_carries_a_membership_item(client):
    meeting_id = _meeting(client, "MTG-MEM-A")
    agenda = client.get(f"/api/meetings/{meeting_id}").get_json()["data"]["agenda"]
    kinds = [item.get("kind") for item in agenda]
    assert "membership" in kinds
    # Before AOB: business, not an afterthought.
    assert kinds.index("membership") < kinds.index("aob")


def test_admin_cannot_grant_a_role_directly(client):
    """The whole point: an administrator proposes, they do not grant."""
    person = _person(client, "Would-be Chair")
    response = client.post(f"{PEOPLE}/{person['item_id']}",
                           json={"fields": {"roles": ["chair"]}, "confirmed": True},
                           headers=HEADERS)
    assert response.status_code == 400
    assert "not set directly" in response.get_json()["error"]


def test_a_proposal_does_not_take_effect_until_ratified(client):
    person = _person(client, "Pending Validator", ["validator"])
    assert not person.get("roles")
    assert roles_for("Pending Validator") == frozenset()


def test_the_committee_sees_what_it_has_to_rule_on(client):
    meeting_id = _meeting(client, "MTG-MEM-B")
    _person(client, "Proposed Owner", ["owner"])
    proposals = client.get(f"/api/meetings/{meeting_id}/membership").get_json()["proposals"]
    mine = next(p for p in proposals if p["name"] == "Proposed Owner")
    assert mine["holds"] == []
    assert mine["proposed"] == ["owner"]


def test_ratifying_grants_the_roles_and_records_the_meeting(client):
    meeting_id = _meeting(client, "MTG-MEM-C")
    person = _person(client, "Ratified Owner", ["owner", "committee"])
    response = client.post(
        f"/api/meetings/{meeting_id}/membership/{person['item_id']}/ratify",
        json={"confirmed": True}, headers=HEADERS)
    assert response.status_code == 200
    listed = client.get("/api/reference").get_json()["data"]["people"]
    updated = next(p for p in listed if p["item_id"] == person["item_id"])
    assert updated["roles"] == ["owner", "committee"]
    assert not updated["pending_roles"]
    # Who granted the seat, which is the question an examiner asks.
    assert updated["roles_ratified_meeting"] == meeting_id
    assert roles_for("Ratified Owner") == frozenset({"owner", "committee"})


def test_declining_leaves_the_roles_a_person_already_holds(client):
    meeting_id = _meeting(client, "MTG-MEM-D")
    person = _person(client, "Aspiring Chair", ["owner"])
    client.post(f"/api/meetings/{meeting_id}/membership/{person['item_id']}/ratify",
                json={"confirmed": True}, headers=HEADERS)
    # Now propose a promotion and have the committee decline it.
    client.post(f"{PEOPLE}/{person['item_id']}",
                json={"fields": {"pending_roles": ["owner", "chair"]}, "confirmed": True},
                headers=HEADERS)
    client.post(f"/api/meetings/{meeting_id}/membership/{person['item_id']}/decline",
                json={"confirmed": True}, headers=HEADERS)
    listed = client.get("/api/reference").get_json()["data"]["people"]
    updated = next(p for p in listed if p["item_id"] == person["item_id"])
    assert updated["roles"] == ["owner"], "declining must not strip what was already granted"
    assert not updated["pending_roles"]


def test_a_ruled_proposal_leaves_the_agenda(client):
    meeting_id = _meeting(client, "MTG-MEM-E")
    person = _person(client, "One And Done", ["reader"])
    client.post(f"/api/meetings/{meeting_id}/membership/{person['item_id']}/ratify",
                json={"confirmed": True}, headers=HEADERS)
    proposals = client.get(f"/api/meetings/{meeting_id}/membership").get_json()["proposals"]
    assert not [p for p in proposals if p["item_id"] == person["item_id"]]


def test_ruling_twice_is_refused(client):
    meeting_id = _meeting(client, "MTG-MEM-F")
    person = _person(client, "Twice Ruled", ["reader"])
    path = f"/api/meetings/{meeting_id}/membership/{person['item_id']}/ratify"
    assert client.post(path, json={"confirmed": True}, headers=HEADERS).status_code == 200
    assert client.post(path, json={"confirmed": True}, headers=HEADERS).status_code == 404


def test_ratification_is_audited(client):
    meeting_id = _meeting(client, "MTG-MEM-G")
    person = _person(client, "Audited Grant", ["administrator"])
    client.post(f"/api/meetings/{meeting_id}/membership/{person['item_id']}/ratify",
                json={"confirmed": True}, headers=HEADERS)
    events = client.get("/api/audit").get_json()
    granting = [e for e in events if meeting_id in str(e.get("payload"))
                and "administrator" in str(e.get("payload"))]
    assert granting, "the grant did not reach the audit trail"
