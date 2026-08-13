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
"""Committee membership and roles: the committee's half of the loop (permissions P2).

A person's roles decide who may own, validate and approve, so granting them is the
committee's decision rather than an administrator's — the same reasoning that sends the
risk policy to the MRC instead of letting Admin set it directly.

Admin -> People proposes (``pending_roles``); this ratifies. Only this path writes
``roles``, which is why that field is readonly everywhere else. Attached to the shared
``mrc_bp`` and pinned to the standing "Committee membership and roles" agenda item.
"""
from __future__ import annotations

from flask import jsonify

from src.governance.mrc import get_meeting_enriched as get_meeting
from src.governance.reference import get_reference_lists, update_option
from src.web._helpers import json_body, request_actor
from src.web.api_mrc._bp import mrc_bp

MEMBERSHIP_KIND = "membership"


def _people_in_scope(meeting: dict) -> list[dict]:
    """People whose roles this committee ratifies.

    A person is anchored to the org tree exactly as a model is, and the committee sees
    the people in its own scope. A Company-level committee sees everybody; a person with
    no division is unanchored and belongs to the company tier rather than to nobody, so
    they are never left without a committee that can grant them a role.
    """
    committee = _committee(meeting)
    people = get_reference_lists().get("people") or []
    if not committee or committee.get("level") == "Company":
        return people
    scope_field = "division" if committee.get("level") == "Division" else "line_of_business"
    wanted = committee.get("scope_value")
    return [p for p in people if p.get(scope_field) == wanted or not p.get("division")]


def _committee(meeting: dict) -> dict | None:
    wanted = (meeting.get("data") or {}).get("mrc")
    for item in get_reference_lists().get("mrc") or []:
        if item.get("value") == wanted:
            return item
    return None


def _proposals(meeting: dict) -> list[dict]:
    """The changes waiting on this committee: everyone in scope with a proposal that
    differs from what they already hold. A proposal identical to the ratified roles is
    not a change and would only clutter the agenda."""
    pending = []
    for person in _people_in_scope(meeting):
        proposed = person.get("pending_roles")
        if proposed is None:
            continue
        if sorted(proposed) == sorted(person.get("roles") or []):
            continue
        pending.append({
            "item_id": person["item_id"],
            "name": person.get("name"),
            "email": person.get("email"),
            "division": person.get("division"),
            "holds": person.get("roles") or [],
            "proposed": proposed,
        })
    return pending


@mrc_bp.get("/<meeting_id>/membership")
def membership_proposals(meeting_id: str):
    """The membership changes this meeting has to rule on."""
    meeting = get_meeting(meeting_id)
    if meeting is None:
        return jsonify({"error": "meeting not found"}), 404
    return jsonify({"meeting_id": meeting_id, "proposals": _proposals(meeting)})


def _rule(meeting_id: str, item_id: str, *, ratify: bool):
    meeting = get_meeting(meeting_id)
    if meeting is None:
        return jsonify({"error": "meeting not found"}), 404
    if (meeting.get("data") or {}).get("status") == "Held":
        return jsonify({"error": "this meeting is closed"}), 400
    proposal = next((p for p in _proposals(meeting) if p["item_id"] == item_id), None)
    if proposal is None:
        return jsonify({"error": "no membership change is pending for that person"}), 404
    body = json_body()
    # Ratifying promotes the proposal to the roles the system acts on and records the
    # meeting that granted it. Declining clears the proposal and leaves the person's
    # current roles untouched — the committee said no, not "start again from nothing".
    fields = (
        {"roles": proposal["proposed"], "pending_roles": None,
         "roles_ratified_meeting": meeting_id}
        if ratify else {"pending_roles": None}
    )
    update_option(
        list_name="people", item_id=item_id, fields=fields,
        actor=request_actor(), reason=body.get("reason"), allow_readonly=True,
    )
    return jsonify({"meeting_id": meeting_id, "proposals": _proposals(get_meeting(meeting_id))})


@mrc_bp.post("/<meeting_id>/membership/<item_id>/ratify")
def ratify_membership(meeting_id: str, item_id: str):
    """The committee grants the proposed roles; they take effect now."""
    return _rule(meeting_id, item_id, ratify=True)


@mrc_bp.post("/<meeting_id>/membership/<item_id>/decline")
def decline_membership(meeting_id: str, item_id: str):
    """The committee declines; the person keeps the roles they already hold."""
    return _rule(meeting_id, item_id, ratify=False)
