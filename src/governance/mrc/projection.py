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
"""MRC-meeting read model: a current-state projection of the event log."""
from __future__ import annotations

from typing import Any

from config.governance import (
    ACTIONS_COLLECTION, CLOSED_ACTION_STATUS, CLOSING_AGENDA_KIND, STANDING_AGENDA,
    STANDING_AGENDA_LIST)
from src.database import read_all, read_view, replace_view
from src.governance.mrc._state import apply, initial_state
from src.governance.mrc.commands import AGGREGATE_TYPE

_VIEW = "mrc_meeting_view"
_COLUMNS = ("meeting_id", "data", "status", "version")


def _to_document(state) -> dict[str, Any]:
    data = dict(state.fields)
    for collection, items in state.collections.items():
        data[collection] = list(items)
    return data


def rebuild_meeting_view(config=None) -> int:
    """Rebuild the read model from the event log; return the meeting count."""
    states: dict[str, tuple] = {}
    for event in read_all(config=config):
        if event.aggregate_type != AGGREGATE_TYPE:
            continue
        state, _ = states.get(event.aggregate_id, (initial_state(), 0))
        state = apply(state, event.event_type, event.payload)
        states[event.aggregate_id] = (state, event.stream_seq)
    rows = ((meeting_id, _to_document(state), state.fields.get("status"), version)
            for meeting_id, (state, version) in states.items())
    return replace_view(_VIEW, _COLUMNS, rows, config=config)


def get_meeting(meeting_id: str, config=None) -> dict[str, Any] | None:
    """Return one meeting's current state, or ``None`` if not present."""
    rows = read_view(_VIEW, _COLUMNS, where="meeting_id", value=meeting_id, config=config)
    return rows[0] if rows else None


def list_meetings(config=None) -> list[dict[str, Any]]:
    """Return all meetings, ordered by ``meeting_id``."""
    return read_view(_VIEW, _COLUMNS, order_by="meeting_id", config=config)


def _standing_order(refs: dict[str, list]) -> list[str]:
    """The kinds a committee runs, in the order it runs them (Admin > Agenda)."""
    kinds = [r.get("kind") for r in (refs.get(STANDING_AGENDA_LIST) or []) if r.get("kind")]
    return kinds or [item["kind"] for item in STANDING_AGENDA]


def _ordered_agenda(agenda: list[dict], refs: dict[str, list]) -> list[dict]:
    """The agenda in the order the committee actually runs it.

    A standing item that reaches a meeting after it was scheduled — a newly shipped
    one, backfilled onto meetings already on the record — is appended, so without
    this it would run last however the committee orders its agenda. Sorting at read
    time rather than rewriting the stored agenda keeps the event log as the record of
    what was actually added, and means the console and the minutes cannot disagree:
    both read through here.

    Deliberately narrow. Standing items are put into the committee's template order,
    but only among the positions they already occupy, and everything else is left
    exactly where it is: an event review, a routed sign-off, an item raised from the
    floor — and, importantly, an item the committee curated into its own running order
    without giving it a kind, which is indistinguishable from a floor item here and
    must not be dragged out of the place its committee chose for it.

    The one thing that does move is the closing item, which is put last whatever was
    added after it was seeded — a meeting does not continue past the point the chair
    closes it.
    """
    order = _standing_order(refs)
    ordered = list(agenda)
    slots = [i for i, item in enumerate(ordered) if (item.get("kind") or "") in order]
    if len(slots) > 1:
        standing = sorted((ordered[i] for i in slots), key=lambda it: order.index(it["kind"]))
        for slot, item in zip(slots, standing):
            ordered[slot] = item
    closing = [i for i in ordered if (i.get("kind") or "") == CLOSING_AGENDA_KIND]
    if closing:
        ordered = [i for i in ordered if (i.get("kind") or "") != CLOSING_AGENDA_KIND] + closing
    return ordered


def _enrich(meeting: dict | None, refs: dict[str, list]) -> dict | None:
    """Overlay the derived org scope onto a meeting, and run its agenda in order."""
    if meeting is None:
        return None
    data = meeting["data"] or {}
    if data.get("agenda"):
        data = {**data, "agenda": _ordered_agenda(data["agenda"], refs)}
    mrc_value = data.get("mrc")
    if mrc_value:
        derived = derive_org_scope(mrc_value, refs)
        if derived:
            data = {**data, **derived}
    meeting["data"] = data
    return meeting


def get_meeting_enriched(meeting_id: str, config=None) -> dict | None:
    """Meeting with company/division / line of business/chair/frequency derived from MRC."""
    from src.governance.reference import get_reference_lists  # avoid import cycle
    return _enrich(get_meeting(meeting_id, config=config), get_reference_lists(config))


def list_meetings_enriched(config=None) -> list[dict]:
    """Every meeting with its MRC-derived fields folded in."""
    from src.governance.reference import get_reference_lists  # avoid import cycle
    refs = get_reference_lists(config)
    return [_enrich(m, refs) for m in list_meetings(config)]


def derive_org_scope(mrc_value: str | None, refs: dict[str, list]) -> dict[str, Any]:
    """Look up a meeting's org scope + chair + frequency from its MRC.

    The MRC reference row carries a level (Company/Division/Line of Business) and a
    scope_value pointing at one Division or Line of Business. Line of Business-level
    committees also resolve their parent Division from the Line of Business
    reference list. Company-level committees are institution-wide and only
    contribute chair + frequency. Returns only the fields we can resolve.
    """
    if not mrc_value:
        return {}
    mrc = next(
        (m for m in refs.get("mrc") or [] if m.get("value") == mrc_value), None,
    )
    if not mrc:
        return {}
    result: dict[str, Any] = {}
    # Chair + frequency + the membership roster all carry through to the meeting,
    # so a meeting knows its committee's members without a second lookup.
    for key in ("chair", "secretary", "frequency", "voting_members", "non_voting_members",
                "quorum_require_chair", "quorum_require_secretary",
                "quorum_min_voting"):
        if mrc.get(key):
            result[key] = mrc[key]
    level, scope = mrc.get("level"), mrc.get("scope_value")
    if level == "Line of Business" and scope:
        lob = next(
            (d for d in refs.get("line_of_business") or [] if d.get("value") == scope), None,
        )
        if lob:
            result["line_of_business"] = lob["value"]
            if lob.get("division"):
                result["division"] = lob["division"]
    elif level == "Division" and scope:
        div = next(
            (v for v in refs.get("division") or [] if v.get("value") == scope), None,
        )
        if div:
            result["division"] = div["value"]
    return result


def matching_mrc(
    division: str | None, line_of_business: str | None, refs: dict[str, list],
) -> tuple[dict[str, Any] | None, str | None]:
    """The most-specific active MRC committee covering an org location.

    The inverse of :func:`derive_org_scope`: given where a model sits, find the
    committee responsible for it. A Line of Business-level committee for the model's
    line_of_business wins; failing that a Division-level committee for its division;
    failing that a Company-level (institution-wide) committee. Archived
    committees are never matched. Returns ``(committee, level)`` or
    ``(None, None)`` when nothing covers it.
    """
    active = [m for m in refs.get("mrc") or [] if m.get("archived") != "true"]
    if line_of_business:
        lob = next(
            (m for m in active
             if m.get("level") == "Line of Business" and m.get("scope_value") == line_of_business),
            None,
        )
        if lob:
            return lob, "Line of Business"
    if division:
        div = next(
            (m for m in active
             if m.get("level") == "Division" and m.get("scope_value") == division),
            None,
        )
        if div:
            return div, "Division"
    company = next((m for m in active if m.get("level") == "Company"), None)
    if company:
        return company, "Company"
    return None, None


def outstanding_actions_for_committee(
    meeting_id: str, config=None
) -> list[dict[str, Any]]:
    """Every action still owed across the committee ``meeting_id`` belongs to.

    An action is agreed at one meeting and answered at a later one, so "what is still
    outstanding" is a question about the committee rather than about any single
    meeting — which is what the standing review item, and the actions carried forward
    into the minutes, both need. Oldest first: a review of outstanding actions starts
    with whatever has been owed longest.

    A meeting with no committee against it stands alone rather than matching every
    other unassigned meeting.
    """
    meetings = list_meetings(config)
    current = next((m for m in meetings if m.get("meeting_id") == meeting_id), None)
    if current is None:
        return []
    committee = (current.get("data") or {}).get("mrc")
    peers = ([m for m in meetings if (m.get("data") or {}).get("mrc") == committee]
             if committee else [current])
    results: list[dict[str, Any]] = []
    for meeting in peers:
        data = meeting.get("data") or {}
        for action in data.get(ACTIONS_COLLECTION) or []:
            if action.get("status") == CLOSED_ACTION_STATUS:
                continue
            results.append({
                **action,
                "meeting_id": meeting["meeting_id"],
                "meeting_title": data.get("title"),
                "meeting_date": data.get("date"),
            })
    results.sort(key=lambda a: (a.get("meeting_date") or "", a.get("item_id") or ""))
    return results


def meeting_items_for_model(
    collection: str, model_id: str, config=None, *, field: str = "model_id",
) -> list[dict[str, Any]]:
    """All items from ``collection`` across every meeting where item[``field``] == ``model_id``.

    Each result is the original item, augmented with the source meeting's id,
    title and date so the model-side read view can credit and link back.

    ``field`` names the key on the item that carries the model reference —
    "model_id" for decisions/actions (default), "subject_model_id" for agenda
    sign-off items (W4c).
    """
    results: list[dict[str, Any]] = []
    for meeting in list_meetings(config):
        data = meeting.get("data") or {}
        for item in data.get(collection) or []:
            if item.get(field) == model_id:
                results.append({
                    **item,
                    "meeting_id": meeting["meeting_id"],
                    "meeting_title": data.get("title"),
                    "meeting_date": data.get("date"),
                })
    return results
