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
"""Meeting lifecycle endpoints: list / get / schedule / update-field / pack.pdf,
the agenda lock, the distribution bundle and agenda-item documents. Attached to the
shared ``mrc_bp``.

What a meeting is ABOUT lives elsewhere: the models in scope and the analysis
presented for each in ``models_scope``, the products in ``products_scope``. This
module is what happens TO a meeting.
"""
from __future__ import annotations

import io
import zipfile
from datetime import date

from flask import Response, jsonify, request, send_file

from src.command import dispatch
from src.files import UploadError, save_upload, upload_path
from src.governance.mrc import (
    get_meeting as get_meeting_raw,
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
from src.web._helpers import context_from_request, json_body, request_actor
from src.web._signoff_routing import drain_pending_for_meeting
from src.web._event_review import allocate_events_for_meeting
from src.web.api_mrc._bp import mrc_bp



@mrc_bp.get("")
def list_all():
    return jsonify(list_meetings())


@mrc_bp.get("/<meeting_id>")
def get_one(meeting_id: str):
    meeting = get_meeting(meeting_id)
    if meeting is None:
        return jsonify({"error": "meeting not found"}), 404
    return jsonify(meeting)


@mrc_bp.get("/<meeting_id>/pack.pdf")
def pack_pdf(meeting_id: str):
    meeting = get_meeting(meeting_id)
    if meeting is None:
        return jsonify({"error": "meeting not found"}), 404
    pdf = render_pack_pdf(meeting, get_settings())
    return Response(pdf, mimetype="application/pdf", headers={
        "Content-Disposition": f'inline; filename="mrc_{meeting_id}.pdf"',
    })


@mrc_bp.post("/<meeting_id>/lock-agenda")
def lock_agenda(meeting_id: str):
    """Chair/secretary finalises the agenda — it becomes read-only and ready to
    distribute. Reversible via unlock-agenda."""
    return _set_agenda_lock(meeting_id, "true")


@mrc_bp.post("/<meeting_id>/unlock-agenda")
def unlock_agenda(meeting_id: str):
    return _set_agenda_lock(meeting_id, "false")


def _set_agenda_lock(meeting_id: str, value: str):
    body = json_body()
    if get_meeting(meeting_id) is None:
        return jsonify({"error": "meeting not found"}), 404
    dispatch(
        "update_meeting_field", update_meeting_field, context=context_from_request(body),
        meeting_id=meeting_id, field="agenda_locked", value=value,
    )
    rebuild_meeting_view()
    return jsonify(get_meeting(meeting_id))


def _meeting_upload_files(meeting: dict) -> list[tuple[str, str, str]]:
    """(category, stored_filename, display_name) for every file uploaded against
    this meeting — agenda item documents and per-model analysis documents."""
    data = meeting["data"] or {}
    files = []
    for a in data.get("agenda") or []:
        if a.get("document_filename"):
            files.append(("meeting_agenda", a["document_filename"],
                          a.get("document_original_name") or a["document_filename"]))
    for m in data.get("models_in_scope") or []:
        if m.get("analysis_filename"):
            files.append(("meeting_analysis", m["analysis_filename"],
                          (m.get("model_id", "") + "_" + (m.get("analysis_original_name")
                                                          or m["analysis_filename"])).lstrip("_")))
    return files


@mrc_bp.get("/<meeting_id>/distribution.zip")
def distribution_zip(meeting_id: str):
    """A distribution pack for members: the agenda PDF plus every uploaded file
    (agenda documents + model analysis documents), bundled as a ZIP."""
    meeting = get_meeting(meeting_id)
    if meeting is None:
        return jsonify({"error": "meeting not found"}), 404
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("agenda.pdf", render_pack_pdf(meeting, get_settings()))
        seen = set()
        for category, filename, display in _meeting_upload_files(get_meeting_raw(meeting_id) or meeting):
            path = upload_path(category, filename)
            if path.exists() and filename not in seen:
                seen.add(filename)
                zf.write(path, arcname="documents/" + display)
    buf.seek(0)
    return Response(buf.read(), mimetype="application/zip", headers={
        "Content-Disposition": f'attachment; filename="mrc_{meeting_id}_distribution.zip"',
    })


def _agenda_item(meeting: dict, item_id: str) -> dict | None:
    return next((a for a in (meeting["data"].get("agenda") or [])
                 if a.get("item_id") == item_id), None)


@mrc_bp.post("/<meeting_id>/agenda/<item_id>/document")
def upload_agenda_document(meeting_id: str, item_id: str):
    """Attach a supporting document to an agenda item."""
    meeting = get_meeting_raw(meeting_id)
    item = _agenda_item(meeting, item_id) if meeting else None
    if item is None:
        return jsonify({"error": "agenda item not found"}), 404
    file = request.files.get("file")
    if file is None:
        return jsonify({"error": "no file provided"}), 400
    try:
        meta = save_upload("meeting_agenda", file.filename, file.read())
    except UploadError as exc:
        return jsonify({"error": str(exc)}), 400
    update_collection_item(
        meeting_id=meeting_id, collection="agenda", item_id=item_id,
        fields={"document_filename": meta["filename"], "document_original_name": meta["original_name"]},
        actor=request_actor(),
    )
    rebuild_meeting_view()
    return jsonify(get_meeting(meeting_id)), 201


@mrc_bp.get("/<meeting_id>/agenda/<item_id>/document")
def download_agenda_document(meeting_id: str, item_id: str):
    """Download an agenda item's supporting document, if uploaded."""
    meeting = get_meeting_raw(meeting_id)
    item = _agenda_item(meeting, item_id) if meeting else None
    if item is None or not item.get("document_filename"):
        return jsonify({"error": "no document uploaded"}), 404
    path = upload_path("meeting_agenda", item["document_filename"])
    if not path.exists():
        # The minutes sign-off item does not carry an uploaded agenda document — it
        # references the previous meeting's minutes, which are stored under the
        # meeting_minutes scope. Fall back to it so the link retrieves that file.
        path = upload_path("meeting_minutes", item["document_filename"])
    if not path.exists():
        return jsonify({"error": "document file missing"}), 404
    return send_file(str(path), as_attachment=True,
                     download_name=item.get("document_original_name") or "document")


@mrc_bp.post("")
def schedule():
    body = json_body()
    meeting_id = body.get("meeting_id")
    ctx = context_from_request(body)
    dispatch(
        "schedule_meeting", schedule_meeting, context=ctx,
        meeting_id=meeting_id, title=body.get("title"), date=body.get("date"),
        fields=body.get("fields") or {},
    )
    rebuild_meeting_view()
    # Seed the standard high-level agenda from the single shared helper, so every
    # creation path (this endpoint and the demo seeder) stays consistent. The
    # detail of model sign-offs and analysis lives in the Models tab, so the
    # agenda stays a running order. Confirmation was already enforced above.
    seed_standing_agenda(meeting_id=meeting_id, actor=ctx.principal.actor, reason=ctx.reason)
    rebuild_meeting_view()
    # Pull any queued sign-off requests for this committee onto the new agenda.
    # (They carry the subject id + proposed RAG but render in the Models tab.)
    drain_pending_for_meeting(ctx, get_meeting_raw(meeting_id) or {"meeting_id": meeting_id, "data": {}})
    # Feed up operational events from this committee's products as agenda items.
    allocate_events_for_meeting(ctx, get_meeting_raw(meeting_id) or {"meeting_id": meeting_id, "data": {}})
    return jsonify(get_meeting(meeting_id)), 201


@mrc_bp.post("/<meeting_id>/field")
def update_field(meeting_id: str):
    body = json_body()
    dispatch(
        "update_meeting_field", update_meeting_field, context=context_from_request(body),
        meeting_id=meeting_id, field=body.get("field"), value=body.get("value"),
    )
    rebuild_meeting_view()
    return jsonify(get_meeting(meeting_id))
