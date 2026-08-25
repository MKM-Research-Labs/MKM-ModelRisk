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
"""Assembling the response queue from the registers (pure).

Takes what the projections and the completeness audit already hold and returns one
list of items, each classified into one of the four states. Nothing here reads a
database: the caller supplies the records, the audit rows, the open committee
actions and the divisions whose policy is unratified, which is what lets the whole
rule be exercised against fixtures.

Three kinds of thing produce an item, and they are deliberately different shapes:

*Records* produce at most one item each — the worst obligation standing against
them (``_rules.worst``). A record that is below standard AND missing its sign-off
is one record needing one response, not two entries on an executive's count.

*Remediation steps and committee actions* produce one item each, because each is a
separate commitment by a named person. Two overdue remediation steps on one record
are two people who have not done what they said they would.

*Divisions* produce one item each where their risk policy has never been ratified.
"""
from __future__ import annotations

from typing import Any

from config.governance import (
    ATTENTION_STATES,
    CLOSED_REMEDIATION_STATUS,
    REASON_COMMITTEE_ACTION_OPEN,
    REASON_POLICY_UNRATIFIED,
    REASON_REMEDIATION_DUE_SOON,
    REASON_REMEDIATION_OVERDUE,
)
from src.governance.attention import _rules

REMEDIATION_COLLECTION = "remediation_steps"


def _entity(record: dict) -> dict[str, Any]:
    """The record's identity as every row carries it — enough to name it on screen
    and to group by it in an ERM, and no more."""
    data = record.get("data") or {}
    return {
        "kind": record.get("kind"),
        "id": record.get("id"),
        "name": record.get("name") or data.get("name") or "",
        "tier": data.get("tier"),
        "rating": data.get("rag_rating"),
        "division": data.get("division"),
    }


def _owner(data: dict) -> str:
    """Whoever answers for the record. A list (an action may have several owners)
    is joined rather than truncated: showing one of three names sends the chase to
    the wrong person."""
    owner = data.get("owner")
    if isinstance(owner, (list, tuple)):
        return ", ".join(str(o) for o in owner if o)
    return str(owner or "")


def _gap_action(row: dict, reason: str) -> str:
    """The audit's own instruction for the gap this reason stands for.

    Read off the gap rather than reworded here, so the queue hands an owner the
    same sentence the signed report does.
    """
    for gap in row.get("gaps") or []:
        if _rules.gap_reasons([gap]) == {reason}:
            return gap.get("action") or ""
    return ""


def _item(*, item_id, reason, entity, owner, due=None, days_over=None,
          action="", committee="", detail="") -> dict[str, Any]:
    """One row of the queue, in the shape both the console and the ERM serialise."""
    return {
        "id": item_id,
        "state": _rules.state_of(reason),
        "reason": reason,
        "reason_label": _rules.label_of(reason),
        # The reason itself when several of these collapse into one row, so a
        # consumer can reproduce the console's rollup or ignore it.
        "group": reason if _rules.is_grouped(reason) else None,
        "entity": entity,
        "owner": owner,
        "committee": committee,
        "due": due,
        "days_over": days_over,
        "detail": detail,
        "action": action or _rules.action_of(reason),
    }


def _record_items(records, audit_by_id, as_of, ages=None) -> list[dict]:
    """At most one item per record: the worst obligation standing against it."""
    items = []
    for record in records:
        data = record.get("data") or {}
        row = audit_by_id.get((record.get("kind"), record.get("id")))
        if row is None:
            # Audited and registered populations are the same by construction. If
            # one ever falls behind the other, a record with no audit row is
            # reported as clear, which is the flattering reading — so skip it and
            # let the count of records disagree visibly instead.
            continue
        reason = _rules.worst(_rules.record_reasons(row, data, as_of, ages))
        if reason is None:
            continue
        # The date only travels on the row when the date is what put it there. A
        # record raised for a missing sign-off does not get its review date printed
        # in the Due column, where it would read as the deadline it is not.
        dated = _rules.review_reason(data, as_of) == reason
        due = data.get("next_review_date") if dated else None
        items.append(_item(
            item_id=f"{reason}:{record.get('kind')}:{record.get('id')}",
            reason=reason, entity=_entity(record), owner=_owner(data),
            due=due, days_over=_rules.days_overdue(due, as_of) if dated else None,
            action=_gap_action(row, reason),
        ))
    return items


def _remediation_items(records, as_of) -> list[dict]:
    """One item per open remediation step that is overdue or coming due.

    A step with no date raises nothing: the committee recorded a commitment
    without one, and inventing a deadline on its behalf would put a date in front
    of an executive that nobody set.
    """
    items = []
    for record in records:
        data = record.get("data") or {}
        entity = _entity(record)
        for step in data.get(REMEDIATION_COLLECTION) or []:
            if step.get("status") == CLOSED_REMEDIATION_STATUS:
                continue
            reason = _rules.due_reason(
                step.get("due_date"), as_of,
                overdue=REASON_REMEDIATION_OVERDUE, soon=REASON_REMEDIATION_DUE_SOON)
            if reason is None:
                continue
            items.append(_item(
                item_id=f"{reason}:{record.get('id')}:{step.get('item_id')}",
                reason=reason, entity=entity, owner=_owner(step),
                due=step.get("due_date"),
                days_over=_rules.days_overdue(step.get("due_date"), as_of),
                detail=step.get("description") or ""))
    return items


def _action_items(committee_actions) -> list[dict]:
    """One item per open committee action. Outstanding, never late — see the note
    on ``REASON_COMMITTEE_ACTION_OPEN``."""
    items = []
    for action in committee_actions or []:
        items.append(_item(
            item_id=f"{REASON_COMMITTEE_ACTION_OPEN}:{action.get('meeting_id')}:"
                    f"{action.get('item_id')}",
            reason=REASON_COMMITTEE_ACTION_OPEN,
            entity={"kind": "Committee action", "id": action.get("item_id"),
                    "name": action.get("description") or "", "tier": None,
                    "rating": None, "division": None,
                    # The meeting it was agreed at, so a row can be opened where it
                    # is minuted rather than dead-ending on an item id.
                    "parent_id": action.get("meeting_id")},
            owner=_owner(action),
            committee=action.get("mrc") or action.get("meeting_title") or "",
            detail=action.get("description") or ""))
    return items


def _division_items(unratified_divisions) -> list[dict]:
    """One item per division running on a policy its committee never ratified."""
    items = []
    for division in unratified_divisions or []:
        name = division.get("division") if isinstance(division, dict) else str(division)
        committee = division.get("committee", "") if isinstance(division, dict) else ""
        chair = division.get("chair", "") if isinstance(division, dict) else ""
        items.append(_item(
            item_id=f"{REASON_POLICY_UNRATIFIED}:{name}",
            reason=REASON_POLICY_UNRATIFIED,
            entity={"kind": "Division", "id": name, "name": name, "tier": None,
                    "rating": None, "division": name},
            owner=chair, committee=committee))
    return items


def build(*, as_of: str, records: list[dict], audit_rows: list[dict],
          committee_actions=None, unratified_divisions=None, ages=None) -> list[dict]:
    """The whole queue, worst state first and stably ordered within a state.

    Ordered by state rather than by severity so the reader meets the four states in
    the order the page presents them; within a state, oldest-owed first, because a
    review of what is outstanding starts with whatever has been owed longest.
    """
    audit_by_id = {(row.get("entity_kind"), row.get("entity_id")): row
                   for row in audit_rows or []}
    items = (_record_items(records, audit_by_id, as_of, ages)
             + _remediation_items(records, as_of)
             + _action_items(committee_actions)
             + _division_items(unratified_divisions))
    order = {state: i for i, state in enumerate(ATTENTION_STATES)}
    items.sort(key=lambda i: (order.get(i["state"], len(order)),
                              -(i["days_over"] or 0), i["id"]))
    return items
