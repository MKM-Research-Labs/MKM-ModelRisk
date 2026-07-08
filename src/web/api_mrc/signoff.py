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


@mrc_bp.post("/<meeting_id>/agenda/<item_id>/approve-signoff")
def approve_signoff(meeting_id: str, item_id: str):
    """Approve a Risk Rating sign-off agenda item (model or product subject).

    Snaps the subject's rag_rating to the proposed value, stamps its MRC sign-off
    date + meeting, records a sign-off history entry, completes the subject's
    queued request, and marks the agenda item Completed — each an auditable event
    under one confirm from the caller.
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
    from_rating = (record["data"] or {}).get("rag_rating")
    meeting_date = meeting["data"].get("date")
    subject.set_field(ctx, subject_id, "rag_rating", proposed_rag)
    history_fields = {"to_rating": proposed_rag, "meeting_id": meeting_id}
    if from_rating:
        history_fields["from_rating"] = from_rating
    if meeting_date:
        history_fields["date"] = meeting_date
    # Approval comments: an explicit ``note`` wins, else fall back to the
    # confirm-dialog ``reason`` so the chair's comment is captured on the
    # sign-off history, not just the audit event.
    note = body.get("note") or body.get("reason")
    if note:
        history_fields["note"] = note
    subject.add_item(ctx, subject_id, "rag_signoff_history", history_fields)
    # Stamp the MRC sign-off: the date, and the meeting it came from (shown as
    # the "MRC sign-off" value in the overview).
    if meeting_date:
        subject.set_field(ctx, subject_id, "mrc_signoff_date", meeting_date)
    subject.set_field(ctx, subject_id, "mrc_signoff_meeting", meeting_id)
    complete_request_for_agenda(ctx, subject, subject_id, item_id)
    dispatch(
        "update_collection_item", update_collection_item, context=ctx,
        meeting_id=meeting_id, collection="agenda", item_id=item_id,
        fields={"status": "Completed"},
    )
    rebuild_meeting_view()
    subject.rebuild()
    return jsonify({"meeting": get_meeting(meeting_id), subject.kind: subject.get(subject_id)})


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
