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
"""Roles are held on the People record, and every change to them is audited (P2).

An administrator PROPOSES roles here; the committee grants them (see
test_membership_ratification_api.py). So these cover the proposal half.
"""
from __future__ import annotations

from src.identity import roles_for
from tests.web.conftest import HEADERS

PEOPLE = "/api/reference/collections/people"


def _add(client, name, roles=None, email=None):
    fields = {"name": name}
    if roles is not None:
        fields["pending_roles"] = roles
    if email:
        fields["email"] = email
    return client.post(PEOPLE, json={"fields": fields, "confirmed": True}, headers=HEADERS)


def _people(client):
    return client.get("/api/reference").get_json()["data"]["people"]


def test_a_person_can_be_proposed_for_several_roles(client):
    """An owner who also sits on a committee is ordinary, not an edge case."""
    assert _add(client, "Ada Owner", ["owner", "committee"]).status_code == 201
    person = next(p for p in _people(client) if p["name"] == "Ada Owner")
    assert person["pending_roles"] == ["owner", "committee"]
    # Proposed only: nothing is granted until the committee says so.
    assert not person.get("roles")


def test_roles_are_optional(client):
    """Registering somebody must not require deciding what they do — P1 only needs them
    to exist."""
    assert _add(client, "Unassigned Person").status_code == 201
    person = next(p for p in _people(client) if p["name"] == "Unassigned Person")
    assert not person.get("roles")
    assert not person.get("pending_roles")


def test_an_invented_role_is_refused(client):
    response = _add(client, "Mallory", ["superuser"])
    assert response.status_code == 400
    assert "superuser" in response.get_json()["error"]


def test_a_role_must_be_a_list_not_a_string(client):
    """"owner,chair" and "owner" would otherwise be the same shape and invite parsing."""
    response = _add(client, "Stringly Typed", "owner")
    assert response.status_code == 400
    assert "list" in response.get_json()["error"]


def test_a_proposal_can_be_withdrawn(client):
    """Thinking better of it before the committee meets is an ordinary admin act."""
    _add(client, "Temporary Chair", ["chair"])
    item_id = next(p["item_id"] for p in _people(client) if p["name"] == "Temporary Chair")
    response = client.post(f"{PEOPLE}/{item_id}",
                           json={"fields": {"pending_roles": []}, "confirmed": True},
                           headers=HEADERS)
    assert response.status_code == 200
    person = next(p for p in _people(client) if p["item_id"] == item_id)
    assert person["pending_roles"] == []


def test_proposing_a_role_is_audited(client):
    """Who ASKED for an approver's seat, alongside who granted it."""
    _add(client, "Audited Person", ["validator"])
    events = client.get("/api/audit").get_json()
    granting = [e for e in events
                if "Audited Person" in str(e.get("payload")) and "validator" in str(e.get("payload"))]
    assert granting, "role assignment did not reach the audit trail"
    assert granting[-1]["actor"] == HEADERS["X-Auth-Request-User"]


def test_a_proposal_grants_nothing_until_it_is_ratified(client):
    """roles_for is what P3 will authorise against, so it must read the GRANTED roles and
    never the proposed ones — otherwise proposing a role would be granting it."""
    _add(client, "Dual Identified", ["administrator"], email="dual@corp")
    assert roles_for("Dual Identified") == frozenset()
    assert roles_for("dual@corp") == frozenset()


def test_an_unregistered_actor_holds_no_roles(client):
    assert roles_for("alice@corp") == frozenset()
