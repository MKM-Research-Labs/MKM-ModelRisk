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
"""Meeting close-out: once quorate with every agenda item resolved, the chair
closes the meeting — this renders and saves the minutes PDF and marks it
Completed. The saved minutes are then served here and offered to the *next*
meeting's previous-minutes sign-off. Attached to the shared ``mrc_bp``."""
from __future__ import annotations

from flask import jsonify, send_file

from src.command import dispatch
from src.files import save_upload, upload_path
from src.governance.mrc import (
    get_meeting_enriched as get_meeting,
    list_meetings_enriched as list_meetings,
    rebuild_meeting_view,
    update_meeting_field,
)
from src.governance.mrc.pack import render_pack_pdf
from src.governance.mrc_settings import get_settings
from src.web._helpers import context_from_request, json_body
from src.web.api_mrc._bp import mrc_bp


def _quorate(d: dict) -> bool:
    """Server-side mirror of the participants-panel quorum rule: Chair +
    Secretary + N voting members marked Attended (non-voting don't count)."""
    parts = {p.get("name"): p for p in (d.get("participants") or [])}
    roster = []
    if d.get("chair"):
        roster.append((d["chair"], "Chair"))
    if d.get("secretary"):
        roster.append((d["secretary"], "Secretary"))
    for n in d.get("voting_members") or []:
        roster.append((n, "Voting"))
    attended: list[str] = []
    seen = set()
    for name, role in roster:
        seen.add(name)
        if ((parts.get(name) or {}).get("status") or "Invited") == "Attended":
            attended.append(role)
    for name, p in parts.items():
        if name not in seen and (p.get("status") or "Invited") == "Attended":
            attended.append(p.get("role") or "Guest")
    req_chair = (d.get("quorum_require_chair") or "Yes") != "No"
    req_sec = (d.get("quorum_require_secretary") or "Yes") != "No"
    try:
        min_voting = int(d.get("quorum_min_voting") or 2)
    except (TypeError, ValueError):
        min_voting = 2
    if req_chair and "Chair" not in attended:
        return False
    if req_sec and "Secretary" not in attended:
        return False
    return attended.count("Voting") >= min_voting


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
    if not _quorate(d):
        return jsonify({"error": "meeting is not quorate"}), 400
    still_open = _open_agenda(d)
    if still_open:
        return jsonify({"error": "agenda items still open: " + ", ".join(still_open)}), 400
    pdf = render_pack_pdf(meeting, get_settings())
    meta = save_upload("meeting_minutes", f"minutes_{meeting_id}.pdf", pdf)
    ctx = context_from_request(body)
    for field, value in (("minutes_filename", meta["filename"]),
                         ("minutes_original_name", meta["original_name"]),
                         ("status", "Completed")):
        dispatch("update_meeting_field", update_meeting_field, context=ctx,
                 meeting_id=meeting_id, field=field, value=value)
    rebuild_meeting_view()
    return jsonify(get_meeting(meeting_id))


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
