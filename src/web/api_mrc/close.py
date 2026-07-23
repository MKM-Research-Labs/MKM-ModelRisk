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
"""Meeting close-out: once quorate with every agenda item resolved, the chair
closes the meeting — this renders and saves the minutes PDF and marks it
Completed. The saved minutes are then served here and offered to the *next*
meeting's previous-minutes sign-off. Attached to the shared ``mrc_bp``."""
from __future__ import annotations

from flask import jsonify, send_file

from src.command import dispatch, require_confirmation
from src.files import save_upload, upload_path
from src.governance.mrc import (
    get_meeting_enriched as get_meeting,
    list_meetings_enriched as list_meetings,
    rebuild_meeting_view,
    schedule_meeting,
    seed_standing_agenda,
    update_collection_item,
    update_meeting_field,
)
from src.governance.mrc.pack import render_pack_pdf
from src.governance.mrc_settings import get_settings
from src.web._helpers import context_from_request, json_body
from src.web.api_mrc._bp import mrc_bp
from src.web.api_mrc._quorum import is_quorate
from src.web.api_mrc._succession import (
    next_date, next_meeting_id, successor_fields, successor_title)


def _open_agenda(d: dict) -> list[str]:
    """Titles of agenda items still Pending (an item is resolved once it is
    Completed / Escalated / Rejected — sign-offs and standing items alike)."""
    return [a.get("title") or a.get("item_id")
            for a in (d.get("agenda") or [])
            if (a.get("status") or "Pending") == "Pending"]


@mrc_bp.post("/<meeting_id>/close")
def close_meeting(meeting_id: str):
    """Close a quorate meeting whose agenda is fully worked through: generate and
    save the minutes PDF, then stamp status Completed (all audited)."""
    body = json_body()
    meeting = get_meeting(meeting_id)
    if meeting is None:
        return jsonify({"error": "meeting not found"}), 404
    d = meeting["data"] or {}
    if d.get("status") == "Completed":
        return jsonify({"error": "meeting is already closed"}), 400
    if not is_quorate(d):
        return jsonify({"error": "meeting is not quorate"}), 400
    still_open = _open_agenda(d)
    if still_open:
        return jsonify({"error": "agenda items still open: " + ", ".join(still_open)}), 400
    ctx = context_from_request(body)
    # Closing is a confirm-to-amend action; gate it before generating the PDF so
    # an unconfirmed call does no work.
    require_confirmation("close_meeting", ctx)
    pdf = render_pack_pdf(meeting, get_settings())
    meta = save_upload("meeting_minutes", f"minutes_{meeting_id}.pdf", pdf)
    for field, value in (("minutes_filename", meta["filename"]),
                         ("minutes_original_name", meta["original_name"]),
                         ("status", "Completed")):
        dispatch("update_meeting_field", update_meeting_field, context=ctx,
                 meeting_id=meeting_id, field=field, value=value)
    rebuild_meeting_view()
    _schedule_successor(meeting_id, d, meta, ctx)
    rebuild_meeting_view()
    return jsonify(get_meeting(meeting_id))


def _previous_minutes_item(meeting_id: str):
    """The successor's standing item for reviewing the previous minutes."""
    fresh = get_meeting(meeting_id) or {}
    for item in (fresh.get("data") or {}).get("agenda") or []:
        if item.get("kind") == "minutes_signoff":
            return item
    return None


def _schedule_successor(meeting_id: str, data: dict, minutes: dict, ctx) -> None:
    """Schedule the next meeting in the cycle and table the minutes just filed.

    Best-effort: the close is already recorded, so a committee with no date or no
    frequency simply gets no successor rather than a failed close.
    """
    current_date = data.get("date")
    if not current_date:
        return
    taken = {m.get("meeting_id") for m in list_meetings()}
    new_id = next_meeting_id(meeting_id, taken)
    if new_id in taken:
        return
    new_date = next_date(current_date, data.get("frequency"))
    title = successor_title(data.get("title") or new_id, meeting_id, new_id, new_date)
    dispatch("schedule_meeting", schedule_meeting, context=ctx, meeting_id=new_id,
             title=title, date=new_date, fields=successor_fields(data))
    dispatch("seed_standing_agenda", seed_standing_agenda, context=ctx, meeting_id=new_id)
    rebuild_meeting_view()
    # File the minutes against the item that exists to review them, so the next
    # chair opens the meeting with the paper already tabled.
    item = _previous_minutes_item(new_id)
    if item is None:
        return
    dispatch("update_collection_item", update_collection_item, context=ctx, meeting_id=new_id,
             collection="agenda", item_id=item["item_id"],
             fields={"document_filename": minutes["filename"],
                     "document_original_name": minutes["original_name"],
                     "prev_minutes_meeting": meeting_id})


@mrc_bp.get("/<meeting_id>/minutes.pdf")
def minutes_pdf(meeting_id: str):
    """Serve the saved minutes PDF (available once the meeting is closed)."""
    meeting = get_meeting(meeting_id)
    if meeting is None:
        return jsonify({"error": "meeting not found"}), 404
    filename = (meeting["data"] or {}).get("minutes_filename")
    if not filename:
        return jsonify({"error": "minutes not generated yet"}), 404
    path = upload_path("meeting_minutes", filename)
    if not path.exists():
        return jsonify({"error": "minutes file missing"}), 404
    return send_file(str(path), mimetype="application/pdf",
                     download_name=f"mrc_{meeting_id}_minutes.pdf")


@mrc_bp.get("/<meeting_id>/prior-minutes")
def prior_minutes(meeting_id: str):
    """Closed meetings of the same committee, dated before this one, that have
    saved minutes — the candidates for the previous-minutes sign-off dropdown."""
    meeting = get_meeting(meeting_id)
    if meeting is None:
        return jsonify({"error": "meeting not found"}), 404
    d = meeting["data"] or {}
    mrc, this_date = d.get("mrc"), d.get("date") or ""
    out = []
    for m in list_meetings():
        md = m.get("data") or {}
        if (md.get("mrc") != mrc or m.get("meeting_id") == meeting_id
                or not md.get("minutes_filename")):
            continue
        if this_date and (md.get("date") or "") >= this_date:
            continue
        out.append({"meeting_id": m.get("meeting_id"), "title": md.get("title"),
                    "date": md.get("date")})
    out.sort(key=lambda r: r.get("date") or "", reverse=True)
    return jsonify(out)
