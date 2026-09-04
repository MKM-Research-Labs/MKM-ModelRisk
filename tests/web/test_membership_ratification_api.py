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
from tests.web._signoff_flows import _schedule_meeting, _seed_mrc
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


# --- Which committee rules on whom --------------------------------------------

def _division_mrc(client, value="MRC-DIV", division="Markets"):
    client.post("/api/reference/collections/mrc",
                json={"fields": {"value": value, "name": value, "level": "Division",
                                 "scope_value": division,
                                 "quorum_require_chair": "No",
                                 "quorum_require_secretary": "No",
                                 "quorum_min_voting": "0"},
                      "confirmed": True}, headers=HEADERS)


def _anchored_person(client, name, division, pending):
    client.post(PEOPLE, json={"fields": {"name": name, "division": division,
                                         "pending_roles": pending},
                              "confirmed": True}, headers=HEADERS)


def test_a_division_committee_rules_on_its_own_division_and_the_unanchored(client):
    """A person anchored elsewhere is another committee's business; a person with
    no division belongs to the company tier rather than to nobody, so they are
    never left without a committee that can grant them a role."""
    _division_mrc(client)
    client.post("/api/meetings",
                json={"meeting_id": "MTG-DIV", "title": "Q1", "date": "2026-09-01",
                      "fields": {"mrc": "MRC-DIV"}, "confirmed": True}, headers=HEADERS)
    _anchored_person(client, "Markets Owner", "Markets", ["owner"])
    _anchored_person(client, "Rates Owner", "Rates", ["owner"])
    _person(client, "Unanchored Reader", ["reader"])

    names = {p["name"] for p in
             client.get("/api/meetings/MTG-DIV/membership").get_json()["proposals"]}
    assert "Markets Owner" in names
    assert "Unanchored Reader" in names
    assert "Rates Owner" not in names


def test_a_proposal_that_changes_nothing_never_reaches_the_agenda(client):
    """Re-proposing what somebody already holds is not a change, and an agenda
    padded with non-decisions is one the committee stops reading."""
    meeting_id = _meeting(client, "MTG-MEM-H")
    person = _person(client, "Already Owner", ["owner"])
    client.post(f"/api/meetings/{meeting_id}/membership/{person['item_id']}/ratify",
                json={"confirmed": True}, headers=HEADERS)
    client.post(f"{PEOPLE}/{person['item_id']}",
                json={"fields": {"pending_roles": ["owner"]}, "confirmed": True},
                headers=HEADERS)
    proposals = client.get(
        f"/api/meetings/{meeting_id}/membership").get_json()["proposals"]
    assert not [p for p in proposals if p["item_id"] == person["item_id"]]


# --- Meetings that cannot rule -------------------------------------------------

def test_membership_for_a_meeting_that_is_not_there_is_404(client):
    assert client.get("/api/meetings/NOPE/membership").status_code == 404


def test_a_ruling_at_a_meeting_that_is_not_there_is_404(client):
    person = _person(client, "Nowhere Ratified", ["reader"])
    assert client.post(
        f"/api/meetings/NOPE/membership/{person['item_id']}/ratify",
        json={"confirmed": True}, headers=HEADERS).status_code == 404


def test_a_closed_meeting_cannot_still_be_granting_seats(client, monkeypatch):
    """A sealed meeting is a finished record. A grant recorded against one after
    the fact would say the committee decided something it never sat for."""
    monkeypatch.setattr("src.governance.mrc.pack.compile_tex",
                        lambda tex, assets=None: b"%PDF-close")
    _seed_mrc(client)
    _schedule_meeting(client, meeting_id="MTG-MEM-I")
    agenda = client.get("/api/meetings/MTG-MEM-I").get_json()["data"]["agenda"]
    for item in agenda:
        client.post(f"/api/meetings/MTG-MEM-I/collections/agenda/{item['item_id']}",
                    json={"fields": {"status": "Completed"}, "confirmed": True},
                    headers=HEADERS)
    assert client.post("/api/meetings/MTG-MEM-I/close",
                       json={"confirmed": True}, headers=HEADERS).status_code == 200

    # Proposed after the committee rose: it is the next meeting's business.
    person = _person(client, "Late Grant", ["reader"])
    refused = client.post(
        f"/api/meetings/MTG-MEM-I/membership/{person['item_id']}/ratify",
        json={"confirmed": True}, headers=HEADERS)
    assert refused.status_code == 400
    assert "closed" in refused.get_json()["error"]
