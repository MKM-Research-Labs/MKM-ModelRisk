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
"""MRC sign-off agenda actions: Approve (W4c) and Escalate (Phase MRC-4)."""
from __future__ import annotations

from flask import jsonify

from src.command import dispatch
from src.governance.mrc import (
    add_collection_item,
    get_meeting_enriched as get_meeting,
    rebuild_meeting_view,
    update_collection_item,
)
from src.web._helpers import context_from_request, json_body
from src.web._signoff_routing import complete_request_for_agenda, subject_for_agenda_item
from src.web.api_mrc._bp import mrc_bp


def _auto_minute(ctx, meeting_id: str, meeting: dict, subject, subject_id: str,
                 record: dict, next_review):
    """Record an approved sign-off as a meeting minute, so the decision lands in
    the log without re-typing. References the subject and the review date set."""
    owner = (record["data"] or {}).get("owner")
    review = next_review or "not set"
    text = (
        f"MRC has reviewed the sign-off request from the {subject.kind} owner"
        + (f" ({owner})" if owner else "")
        + f" and has granted approval and has set a date of next review on {review}."
    )
    fields = {"title": f"Sign-off approved — {subject_id}", "text": text,
              subject.id_key: subject_id}
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

    Every decision records a sign-off history entry (with the outcome + any
    next-review date the committee set) and moves the queued request + agenda
    item to their terminal state. An approval additionally snaps the subject's
    rag_rating and stamps its MRC sign-off date + meeting. All auditable events
    under one confirm.
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
    subject, subject_id = subject_for_agenda_item(item)
    if subject is None or not proposed_rag:
        return jsonify({"error": "agenda item is not a sign-off request"}), 400
    record = subject.get(subject_id)
    if record is None:
        return jsonify({"error": f"subject {subject_id} not found"}), 404
    ctx = context_from_request(body)
    approved = outcome == "Approved"
    from_rating = (record["data"] or {}).get("rag_rating")
    meeting_date = meeting["data"].get("date")
    next_review = body.get("next_review_date")
    # An approval promotes the proposed rating; a rejection leaves it untouched.
    if approved:
        subject.set_field(ctx, subject_id, "rag_rating", proposed_rag)
    history_fields = {"to_rating": proposed_rag, "meeting_id": meeting_id, "outcome": outcome}
    if from_rating:
        history_fields["from_rating"] = from_rating
    if meeting_date:
        history_fields["date"] = meeting_date
    if next_review:
        history_fields["next_review_date"] = next_review
    # Comments: an explicit ``note`` wins, else the confirm-dialog ``reason``.
    note = body.get("note") or body.get("reason")
    if note:
        history_fields["note"] = note
    subject.add_item(ctx, subject_id, "rag_signoff_history", history_fields)
    # The committee sets the next review date on either outcome.
    if next_review:
        subject.set_field(ctx, subject_id, "next_review_date", next_review)
    # An approval stamps the MRC sign-off (date + the meeting it came from).
    if approved:
        if meeting_date:
            subject.set_field(ctx, subject_id, "mrc_signoff_date", meeting_date)
        subject.set_field(ctx, subject_id, "mrc_signoff_meeting", meeting_id)
        _auto_minute(ctx, meeting_id, meeting, subject, subject_id, record, next_review)
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
