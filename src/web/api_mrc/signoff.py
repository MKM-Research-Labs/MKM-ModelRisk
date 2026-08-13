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
"""MRC sign-off agenda actions: Approve (W4c) and Escalate (Phase MRC-4)."""
from __future__ import annotations

from flask import jsonify

from src.command import dispatch, require_confirmation
from src.governance.mrc import (
    add_collection_item,
    get_meeting_enriched as get_meeting,
    rebuild_meeting_view,
    update_collection_item,
)
from src.web._helpers import context_from_request, json_body
from src.web._signoff_routing import (
    HISTORY,
    complete_request_for_agenda,
    subject_for_agenda_item,
)
from src.web.api_mrc._bp import mrc_bp
from src.web.api_mrc._quorum import is_quorate


def _review_received(record: dict) -> str:
    """What the minute says about the review the committee was given, if any.

    The committee signs off the risk rating; the Model Review Report is the
    evidence in front of it when it does. Naming the report — and who signed it,
    and when — is what makes the minute show the rating was granted on a basis,
    rather than leaving a reader to hope one existed.
    """
    signoffs = (record.get("data") or {}).get("review_signoffs") or []
    if not signoffs:
        return ""
    latest = signoffs[-1]
    signed_at = (latest.get("signed_at") or "")[:10]
    return (" MRC received the Model Review Report signed off by "
            f"{latest.get('signed_by') or 'the reviewer'}"
            f"{' on ' + signed_at if signed_at else ''}.")


def _minute_text(signoff_kind: str, subject, subject_id: str, owner_bit: str,
                 next_review, review_bit: str = "") -> tuple[str, str]:
    """The title + wording recording what the committee ratified."""
    if signoff_kind == "owner":
        return (
            f"Model owner ratified — {subject_id}",
            f"MRC has reviewed the change of {subject.kind} owner for {subject_id} and "
            "has ratified the appointment. The new owner answers for the model from "
            "the date of the change, which the record already shows.",
        )
    if signoff_kind == "retire":
        return (
            f"Retire ratified — {subject_id}",
            f"MRC has reviewed the retire request from the {subject.kind} owner"
            f"{owner_bit} and has ratified it. The {subject.kind} is hibernated "
            f"and drops out of the active inventory.",
        )
    if signoff_kind == "reactivate":
        return (
            f"Reactivate ratified — {subject_id}",
            f"MRC has reviewed the reactivate request from the {subject.kind} owner"
            f"{owner_bit} and has ratified it. The {subject.kind} returns to the "
            f"active inventory.",
        )
    if signoff_kind == "handoff":
        return (
            f"Handoff compatibility approved — {subject_id}",
            f"MRC has reviewed the field lineage and compatibility of the model "
            f"handoff {subject_id}{owner_bit} and has approved it as compatible.",
        )
    return (
        f"Sign-off approved — {subject_id}",
        f"MRC has reviewed the sign-off request from the {subject.kind} owner"
        f"{owner_bit} and has granted approval and has set a date of next review "
        f"on {next_review or 'not set'}." + review_bit,
    )


def _auto_minute(ctx, meeting_id: str, meeting: dict, subject, subject_id: str,
                 record: dict, next_review, signoff_kind: str = "rag"):
    """Record an approved decision as a meeting minute, so it lands in the log
    without re-typing. The wording reflects what was actually ratified."""
    owner = (record["data"] or {}).get("owner")
    owner_bit = f" ({owner})" if owner else ""
    title, text = _minute_text(signoff_kind, subject, subject_id, owner_bit, next_review,
                               _review_received(record))
    fields = {"title": title, "text": text, subject.id_key: subject_id}
    chair = meeting["data"].get("chair")
    if chair:
        fields["presenter"] = chair
    # File the minute under the "Review model sign-off" standing agenda item so
    # the Minutes tab reads as a walk-through of the agenda.
    review_item = next(
        (a for a in (meeting["data"].get("agenda") or [])
         if a.get("kind") == "review_signoff"
         or (a.get("title") or "").lower() == "review model sign-off"),
        None,
    )
    if review_item:
        fields["agenda_item_id"] = review_item.get("item_id")
    dispatch(
        "add_collection_item", add_collection_item, context=ctx,
        meeting_id=meeting_id, collection="minutes", fields=fields,
    )


def _decide_signoff(meeting_id: str, item_id: str, *, outcome: str):
    """Record the committee's decision on a sign-off item (Approved / Rejected)
    for a model or product subject, and reflect it back onto that subject.

    One queue carries every kind of decision, so what an approval *does* follows
    the item's ``signoff_kind``: "rag" snaps the subject's rag_rating and stamps
    its MRC sign-off date + meeting; "retire" hibernates it; "reactivate" brings
    it back. Whatever the kind, the decision records a history entry (with the
    outcome + any next-review date), is minuted, and moves the queued request +
    agenda item to their terminal state — all auditable events under one confirm.
    """
    body = json_body()
    meeting = get_meeting(meeting_id)
    if meeting is None:
        return jsonify({"error": "meeting not found"}), 404
    agenda = meeting["data"].get("agenda") or []
    item = next((a for a in agenda if a.get("item_id") == item_id), None)
    if item is None:
        return jsonify({"error": "agenda item not found"}), 404
    proposed_rag = item.get("proposed_rag")
    # What the committee is being asked to ratify. Items raised before the queue
    # carried a kind are rating decisions, which is what a proposed_rag implies.
    signoff_kind = item.get("signoff_kind") or ("rag" if proposed_rag else None)
    subject, subject_id = subject_for_agenda_item(item)
    if subject is None or not signoff_kind:
        return jsonify({"error": "agenda item is not a sign-off request"}), 400
    if not subject.supports(signoff_kind):
        return jsonify(
            {"error": f"a {subject.kind} cannot be the subject of a "
                      f"{signoff_kind} decision"}
        ), 400
    # A committee may only take sign-off decisions once the meeting is quorate —
    # the same gate that governs closing it. Enforced here, not just in the UI,
    # so the "wait until the meeting is quorate" rule can't be bypassed.
    if not is_quorate(meeting["data"]):
        return jsonify({"error": "meeting is not quorate"}), 400
    record = subject.get(subject_id)
    if record is None:
        return jsonify({"error": f"subject {subject_id} not found"}), 404
    ctx = context_from_request(body)
    # A committee decision is a confirm-to-amend action (composed of several
    # sub-commands), so gate it explicitly before any of them mutate.
    require_confirmation("signoff", ctx)
    approved = outcome == "Approved"
    from_rating = (record["data"] or {}).get("rag_rating")
    meeting_date = meeting["data"].get("date")
    next_review = body.get("next_review_date")
    # An approval carries out what was asked; a rejection changes nothing about
    # the subject beyond recording the decision.
    if approved:
        if signoff_kind == "retire":
            subject.retire(ctx, subject_id)
        elif signoff_kind == "reactivate":
            subject.reactivate(ctx, subject_id)
        elif signoff_kind == "rag":
            subject.set_field(ctx, subject_id, "rag_rating", proposed_rag)
        # "handoff" carries no field to snap — approving it is recorded by the
        # MRC sign-off stamp below, which is what makes the handoff "Approved".
        # "owner" carries none either: the new owner took the model when the change
        # was made, because a model cannot sit unowned while a committee meets. What
        # the approval settles is whether the appointment stands.
    history_fields = {"kind": signoff_kind, "meeting_id": meeting_id, "outcome": outcome}
    # The rating fields only mean anything for a rating decision.
    if signoff_kind == "rag":
        history_fields["to_rating"] = proposed_rag
        if from_rating:
            history_fields["from_rating"] = from_rating
    # An owner decision records the change it ratified, so the history says who
    # handed the model to whom rather than merely that something was approved.
    if signoff_kind == "owner":
        for key in ("from_owner", "to_owner"):
            if item.get(key):
                history_fields[key] = item[key]
    if meeting_date:
        history_fields["date"] = meeting_date
    if next_review:
        history_fields["next_review_date"] = next_review
    # Comments: an explicit ``note`` wins, else the confirm-dialog ``reason``.
    note = body.get("note") or body.get("reason")
    if note:
        history_fields["note"] = note
    subject.add_item(ctx, subject_id, HISTORY, history_fields)
    # The committee sets the next review date on either outcome.
    if next_review:
        subject.set_field(ctx, subject_id, "next_review_date", next_review)
    # An approved *rating* stamps the MRC sign-off (date + the meeting it came
    # from); a retire/reactivate is not a rating sign-off, so it leaves the stamp
    # alone — but every ratified decision is minuted.
    if approved:
        if signoff_kind in ("rag", "handoff"):
            if meeting_date:
                subject.set_field(ctx, subject_id, "mrc_signoff_date", meeting_date)
            subject.set_field(ctx, subject_id, "mrc_signoff_meeting", meeting_id)
        _auto_minute(ctx, meeting_id, meeting, subject, subject_id, record,
                     next_review, signoff_kind)
    complete_request_for_agenda(ctx, subject, subject_id, item_id,
                                status=("Completed" if approved else "Rejected"))
    dispatch(
        "update_collection_item", update_collection_item, context=ctx,
        meeting_id=meeting_id, collection="agenda", item_id=item_id,
        fields={"status": ("Completed" if approved else "Rejected")},
    )
    rebuild_meeting_view()
    subject.rebuild()
    return jsonify({"meeting": get_meeting(meeting_id), subject.kind: subject.get(subject_id)})


@mrc_bp.post("/<meeting_id>/agenda/<item_id>/approve-signoff")
def approve_signoff(meeting_id: str, item_id: str):
    """Grant a Risk Rating sign-off (model or product subject)."""
    return _decide_signoff(meeting_id, item_id, outcome="Approved")


@mrc_bp.post("/<meeting_id>/agenda/<item_id>/reject-signoff")
def reject_signoff(meeting_id: str, item_id: str):
    """Reject a Risk Rating sign-off — the rating is not promoted; the request
    and agenda item are marked Rejected and reflected back onto the subject."""
    return _decide_signoff(meeting_id, item_id, outcome="Rejected")


@mrc_bp.post("/<meeting_id>/agenda/<item_id>/escalate-signoff")
def escalate_signoff(meeting_id: str, item_id: str):
    """Phase MRC-4: Escalate a sign-off request to a higher-tier MRC meeting.

    Copies the sign-off (same subject_model_id + proposed_rag) as a new
    Pending agenda item on the target parent meeting, and marks the original
    Escalated. Two events, one confirm from the caller.
    """
    body = json_body()
    parent_meeting_id = body.get("parent_meeting_id")
    if not parent_meeting_id:
        return jsonify({"error": "parent_meeting_id is required"}), 400
    meeting = get_meeting(meeting_id)
    if meeting is None:
        return jsonify({"error": "meeting not found"}), 404
    agenda = meeting["data"].get("agenda") or []
    item = next((a for a in agenda if a.get("item_id") == item_id), None)
    if item is None:
        return jsonify({"error": "agenda item not found"}), 404
    subject, subject_id = subject_for_agenda_item(item)
    if subject is None or not item.get("proposed_rag"):
        return jsonify({"error": "agenda item is not a sign-off request"}), 400
    parent = get_meeting(parent_meeting_id)
    if parent is None:
        return jsonify({"error": "parent meeting not found"}), 404
    if parent["status"] != "Scheduled":
        return jsonify({"error": "can only escalate to a Scheduled meeting"}), 400
    if parent_meeting_id == meeting_id:
        return jsonify({"error": "cannot escalate a meeting to itself"}), 400
    ctx = context_from_request(body)
    dispatch(
        "add_collection_item", add_collection_item, context=ctx,
        meeting_id=parent_meeting_id, collection="agenda",
        fields={
            "title": f"[Escalated] Risk rating sign-off: {subject_id} "
                     f"→ {item['proposed_rag']}",
            subject.agenda_id_field: subject_id,
            "proposed_rag": item["proposed_rag"],
            "status": "Pending",
            "escalated_from_meeting_id": meeting_id,
            "escalated_from_agenda_id": item_id,
        },
    )
    dispatch(
        "update_collection_item", update_collection_item, context=ctx,
        meeting_id=meeting_id, collection="agenda", item_id=item_id,
        fields={"status": "Escalated"},
    )
    rebuild_meeting_view()
    return jsonify({"meeting": get_meeting(meeting_id), "parent": get_meeting(parent_meeting_id)})
