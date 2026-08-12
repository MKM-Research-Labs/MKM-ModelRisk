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
"""The life of an agreed action: dated updates with optional supporting evidence,
and the committee's ratification of a requested closure.

An action is raised by the committee and worked by its owners, who record progress as
updates. When the owners believe it is done they move it to "Closure requested" — they
cannot close it themselves (``_rules._require_closure_is_ratified``). The committee
settles it here, quorate and confirmed, and the closure is minuted like any other
decision it takes.
"""
from __future__ import annotations

from datetime import date

from flask import jsonify, request, send_file

from config.governance import (
    ACTION_EVIDENCE_SCOPE,
    ACTIONS_COLLECTION,
    CLOSED_ACTION_STATUS,
    DEFAULT_ACTION_STATUS,
    REQUESTED_CLOSURE_ACTION_STATUS,
)
from src.command import dispatch, require_confirmation
from src.files import UploadError, save_upload, upload_path
from src.governance.mrc import (
    add_collection_item,
    get_meeting as get_meeting_raw,
    get_meeting_enriched as get_meeting,
    outstanding_actions_for_committee,
    rebuild_meeting_view,
    update_collection_item,
)
from src.web._helpers import context_from_request, json_body, request_actor
from src.web.api_mrc._bp import mrc_bp
from src.web.api_mrc._quorum import is_quorate


def _action(meeting: dict, item_id: str) -> dict | None:
    return next((a for a in (meeting["data"].get(ACTIONS_COLLECTION) or [])
                 if a.get("item_id") == item_id), None)


def _appended(action: dict, entry: dict) -> list[dict]:
    """The action's update history with ``entry`` on the end.

    The history is append-only in practice: an update records what was true on a date,
    so correcting it means adding another, not rewriting the one already minuted.
    """
    return list(action.get("updates") or []) + [entry]


@mrc_bp.post("/<meeting_id>/collections/actions/<item_id>/updates")
def add_action_update(meeting_id: str, item_id: str):
    """Append a dated update to an action, optionally carrying a supporting file.

    Multipart rather than JSON because the evidence travels with the note that explains
    it: a file with no note is an orphan, and a closure request whose evidence arrived
    as a separate anonymous upload is worse than one with none. The date is stamped
    here rather than taken from the client — it is a record of when this was said.
    """
    meeting = get_meeting_raw(meeting_id)
    if meeting is None:
        return jsonify({"error": "meeting not found"}), 404
    action = _action(meeting, item_id)
    if action is None:
        return jsonify({"error": "action not found"}), 404
    note = (request.form.get("note") or "").strip()
    status = (request.form.get("status") or "").strip() or action.get("status")
    entry = {"date": date.today().isoformat(), "note": note, "status": status}

    file = request.files.get("file")
    if file is not None and file.filename:
        try:
            meta = save_upload(ACTION_EVIDENCE_SCOPE, file.filename, file.read())
        except UploadError as exc:
            return jsonify({"error": str(exc)}), 400
        entry["filename"] = meta["filename"]
        entry["original_name"] = meta["original_name"]
    elif not note:
        return jsonify({"error": "an update needs a note, a file, or both"}), 400

    # The domain refuses a status of Closed here — an owner requests closure, the
    # committee grants it — so this path never needs to know that rule itself.
    update_collection_item(
        meeting_id=meeting_id, collection=ACTIONS_COLLECTION, item_id=item_id,
        fields={"updates": _appended(action, entry), "status": status},
        actor=request_actor(),
    )
    rebuild_meeting_view()
    return jsonify(get_meeting(meeting_id)), 201


@mrc_bp.get("/<meeting_id>/collections/actions/<item_id>/evidence/<filename>")
def download_action_evidence(meeting_id: str, item_id: str, filename: str):
    """Download one update's supporting file.

    Served by the name recorded on the update rather than by a bare path, so a file
    can only be fetched through the action it evidences.
    """
    meeting = get_meeting_raw(meeting_id)
    action = _action(meeting, item_id) if meeting else None
    if action is None:
        return jsonify({"error": "action not found"}), 404
    entry = next((u for u in (action.get("updates") or [])
                  if u.get("filename") == filename), None)
    if entry is None:
        return jsonify({"error": "no such evidence on this action"}), 404
    path = upload_path(ACTION_EVIDENCE_SCOPE, entry["filename"])
    if not path.exists():
        return jsonify({"error": "evidence file missing"}), 404
    return send_file(str(path), as_attachment=True,
                     download_name=entry.get("original_name") or entry["filename"])


@mrc_bp.get("/<meeting_id>/outstanding-actions")
def outstanding_actions(meeting_id: str):
    """Every action still owed across this committee, oldest first.

    What the standing review item shows, and what the minutes carry forward: an
    action agreed at one meeting is answered at a later one, so this deliberately
    reaches across the committee's meetings rather than reading only this one.
    """
    if get_meeting(meeting_id) is None:
        return jsonify({"error": "meeting not found"}), 404
    return jsonify(outstanding_actions_for_committee(meeting_id))


def _decide_closure(meeting_id: str, granted: bool):
    """Shared body of ratify / reject — the committee's answer to a closure request.

    ``meeting_id`` is the meeting TAKING the decision. The action itself usually lives
    on an earlier meeting (that is the point of reviewing outstanding actions), so the
    status is written there while the minute is recorded here, against the committee
    that actually decided it.
    """
    body = json_body()
    source_id = body.get("source_meeting_id") or meeting_id
    item_id = body.get("item_id") or ""
    # The enriched meeting, because quorum is judged against the committee's roster
    # (chair, secretary, voting members), which the raw record does not carry.
    meeting = get_meeting(meeting_id)
    if meeting is None:
        return jsonify({"error": "meeting not found"}), 404
    source = get_meeting(source_id)
    action = _action(source, item_id) if source else None
    if action is None:
        return jsonify({"error": "action not found"}), 404
    if action.get("status") != REQUESTED_CLOSURE_ACTION_STATUS:
        return jsonify({"error": "closure has not been requested for this action"}), 400
    if not is_quorate(meeting["data"]):
        return jsonify({"error": "meeting is not quorate"}), 400
    ctx = context_from_request(body)
    # Composed op (several sub-commands) — gate it once before anything mutates.
    require_confirmation("decide_action_closure", ctx)
    note = (body.get("comments") or "").strip()

    status = CLOSED_ACTION_STATUS if granted else DEFAULT_ACTION_STATUS
    default_note = ("Closure ratified by the committee" if granted
                    else "Closure declined by the committee; the action stays open")
    entry = {"date": date.today().isoformat(), "note": note or default_note,
             "status": status}
    dispatch(
        "update_collection_item", update_collection_item, context=ctx,
        meeting_id=source_id, collection=ACTIONS_COLLECTION, item_id=item_id,
        fields={"updates": _appended(action, entry), "status": status},
        ratifying=granted,
    )
    verb = "ratified the closure of" if granted else "declined to close"
    text = f"MRC {verb} action {item_id}: {action.get('description', '')}".strip()
    if source_id != meeting_id:
        text += f" (agreed at {source_id})"
    if note:
        text += " " + note
    title = ("Action closed" if granted else "Closure declined") + f" — {item_id}"
    dispatch(
        "add_collection_item", add_collection_item, context=ctx,
        meeting_id=meeting_id, collection="minutes",
        fields={"title": title, "text": text, "model_id": action.get("model_id", "")},
    )
    rebuild_meeting_view()
    return jsonify(get_meeting(meeting_id))


@mrc_bp.post("/<meeting_id>/action-closures/ratify")
def ratify_action_closure(meeting_id: str):
    """Close an action the committee is satisfied is done — the one writer of the
    closed status, gated exactly as the committee's other decisions are."""
    return _decide_closure(meeting_id, granted=True)


@mrc_bp.post("/<meeting_id>/action-closures/reject")
def reject_action_closure(meeting_id: str):
    """Decline a requested closure: the action returns to open, and the committee's
    reason is minuted so the owner can see why it was not accepted."""
    return _decide_closure(meeting_id, granted=False)
