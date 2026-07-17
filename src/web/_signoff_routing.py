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
"""Sign-off request routing, shared by models and products.

A Risk-rating sign-off request is raised by an owner and queued on the subject
(a model or a product) against its responsible MRC (``signoff_requests``). It
waits as ``Pending`` until a meeting of that committee is scheduled, at which
point it is pulled onto the agenda and marked ``Attached``; when the committee
approves, the subject's rating/date are stamped and the request is ``Completed``.

Model and product are the same workflow over different aggregates, so a small
``Subject`` adapter captures the per-aggregate differences (which command to
dispatch, which agenda field carries the subject id). This module imports only
governance functions (no blueprints) to stay cycle-free.
"""
from __future__ import annotations

from datetime import date


from config.governance import SIGNOFF_HISTORY_COLLECTION, SIGNOFF_REQUESTS_COLLECTION
from src.command import CommandContext, dispatch
# The adapter moved to its own module, but this stays the front door for the
# whole sign-off flow — re-exported so call sites import the routing and its
# subjects from one place.
from src.web._signoff_subject import (  # noqa: F401
    MODEL_SUBJECT,
    PRODUCT_SUBJECT,
    SUBJECTS,
    Subject,
    subject_for_agenda_item,
)
from src.governance.mrc import (
    add_collection_item as _mrc_add,
    get_meeting,
    list_meetings,
    rebuild_meeting_view,
)


# The single approvals queue (every kind of decision the committee ratifies) and
# the audit of what it decided. Named in config so the domain rules and this
# routing cannot disagree about them.
REQUESTS = SIGNOFF_REQUESTS_COLLECTION
HISTORY = SIGNOFF_HISTORY_COLLECTION


def _newest(items: list[dict]) -> dict | None:
    """The item with the highest generated id suffix (e.g. SR-003 over SR-001)."""
    def _seq(item: dict) -> int:
        try:
            return int(str(item.get("item_id", "")).rsplit("-", 1)[-1])
        except ValueError:
            return -1
    return max(items, key=_seq) if items else None


def earliest_scheduled_for_mrc(target_mrc: str, config=None) -> dict | None:
    """The soonest Scheduled meeting bound to ``target_mrc`` (by date), if any."""
    scheduled = [
        m for m in list_meetings(config)
        if m.get("status") == "Scheduled" and (m["data"] or {}).get("mrc") == target_mrc
    ]
    scheduled.sort(key=lambda m: (m["data"] or {}).get("date") or "9999-99-99")
    return scheduled[0] if scheduled else None


def raise_signoff(ctx: CommandContext, subject: Subject, subject_id: str, *,
                  target_mrc: str, kind: str = "rag", proposed_rag: str | None = None,
                  note: str | None = None) -> dict | None:
    """Queue a sign-off request on the subject and attach it if a meeting exists.

    ``kind`` is what the committee is being asked to ratify (see
    VALID_SIGNOFF_KINDS); ``proposed_rag`` only applies to a rating request.
    """
    fields = {"kind": kind, "target_mrc": target_mrc, "status": "Pending"}
    if proposed_rag:
        fields["proposed_rag"] = proposed_rag
    if note:
        fields["note"] = note
    subject.add_item(ctx, subject_id, REQUESTS, fields)
    subject.rebuild()
    refreshed = subject.get(subject_id) or {"data": {}}
    request = _newest(refreshed["data"].get(REQUESTS) or [])
    meeting = earliest_scheduled_for_mrc(target_mrc)
    if meeting is not None and request is not None:
        attach_request(ctx, subject, subject_id, request, meeting)
    return subject.get(subject_id)


def revoke_signoff(ctx: CommandContext, subject: Subject, subject_id: str, *,
                   note: str | None = None, on_date: str | None = None) -> dict | None:
    """Revoke a granted MRC sign-off. Appends a ``Revoked`` sign-off-history entry
    and clears the MRC sign-off stamp (date + meeting). The rag_rating is kept —
    this un-approves the rating rather than re-rating it, so the subject returns
    to needing sign-off. Guarding that it *is* currently signed off is the
    caller's job."""
    record = subject.get(subject_id) or {"data": {}}
    current = (record["data"] or {}).get("rag_rating")
    # to_rating is a required history field; a revoke is recorded *at* the current
    # rating (from == to), the outcome is what flips ``signed_off`` off.
    fields = {"kind": "rag", "outcome": "Revoked",
              "date": on_date or date.today().isoformat(),
              "to_rating": current, "from_rating": current}
    if note:
        fields["note"] = note
    subject.add_item(ctx, subject_id, HISTORY, fields)
    subject.set_field(ctx, subject_id, "mrc_signoff_date", "")
    subject.set_field(ctx, subject_id, "mrc_signoff_meeting", "")
    subject.rebuild()
    return subject.get(subject_id)


def agenda_title(signoff_kind: str, subject_id: str, proposed_rag: str | None) -> str:
    """How the decision reads on the committee's agenda."""
    if signoff_kind == "retire":
        return f"Retire (hibernate): {subject_id}"
    if signoff_kind == "reactivate":
        return f"Reactivate: {subject_id}"
    return f"Risk rating sign-off: {subject_id} → {proposed_rag}"


def attach_request(ctx: CommandContext, subject: Subject, subject_id: str,
                   request_item: dict, meeting: dict, config=None) -> None:
    """Put a queued request onto a meeting's agenda and mark it Attached."""
    meeting_id = meeting["meeting_id"]
    proposed = request_item.get("proposed_rag")
    signoff_kind = request_item.get("kind") or "rag"
    fields = {
        "title": agenda_title(signoff_kind, subject_id, proposed),
        subject.agenda_id_field: subject_id,
        "signoff_kind": signoff_kind,
        "status": "Pending",
    }
    # Only a rating decision carries a proposed rating.
    if proposed:
        fields["proposed_rag"] = proposed
    dispatch(
        "add_collection_item", _mrc_add, context=ctx,
        meeting_id=meeting_id, collection="agenda", fields=fields,
    )
    rebuild_meeting_view(config)
    refreshed = get_meeting(meeting_id, config=config) or {"data": {}}
    # Match on the subject + what is being decided. A retire has no rating, so
    # matching on proposed_rag alone would never find its item.
    agenda = [
        a for a in (refreshed["data"].get("agenda") or [])
        if a.get(subject.agenda_id_field) == subject_id
        and (a.get("signoff_kind") or "rag") == signoff_kind
        and a.get("proposed_rag") == proposed
    ]
    agenda_item = _newest(agenda)
    subject.update_item(
        ctx, subject_id, REQUESTS, request_item["item_id"],
        {"status": "Attached", "meeting_id": meeting_id,
         "agenda_item_id": (agenda_item or {}).get("item_id", "")},
    )
    subject.rebuild()


def complete_request_for_agenda(ctx: CommandContext, subject: Subject, subject_id: str,
                                agenda_item_id: str, status: str = "Completed", config=None) -> None:
    """Move the subject's queued request to a terminal status (Completed /
    Rejected) once the committee decides on its agenda item."""
    fresh = subject.get(subject_id) or {"data": {}}
    request = next(
        (r for r in (fresh["data"].get(REQUESTS) or [])
         if r.get("agenda_item_id") == agenda_item_id and r.get("status") == "Attached"),
        None,
    )
    if request is not None:
        subject.update_item(ctx, subject_id, REQUESTS,
                            request["item_id"], {"status": status})
        subject.rebuild()


def drain_pending_for_meeting(ctx: CommandContext, meeting: dict, config=None) -> int:
    """Attach every Pending request (models + products) for this meeting's MRC."""
    target_mrc = (meeting.get("data") or {}).get("mrc")
    if not target_mrc:
        return 0
    attached = 0
    for subject in SUBJECTS:
        for row in subject.list_all():
            data = row.get("data") or {}
            for req in data.get(REQUESTS) or []:
                if req.get("status") == "Pending" and req.get("target_mrc") == target_mrc:
                    fresh = subject.get(row[subject.id_key]) or {"data": {}}
                    current = next(
                        (r for r in (fresh["data"].get(REQUESTS) or [])
                         if r.get("item_id") == req.get("item_id")),
                        None,
                    )
                    if current and current.get("status") == "Pending":
                        attach_request(ctx, subject, row[subject.id_key], current, meeting, config=config)
                        attached += 1
    return attached
