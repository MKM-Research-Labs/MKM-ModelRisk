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
"""Meeting lifecycle endpoints: list / get / schedule / update-field / pack.pdf
/ models-in-scope (the projection join). Attached to the shared ``mrc_bp``."""
from __future__ import annotations

from datetime import date

from flask import Response, jsonify, request, send_file

from src.command import dispatch
from src.files import UploadError, save_upload, upload_path
from src.governance.model_inventory import get_model
from src.governance.model_inventory.review import compute_review_status
from src.governance.mrc import (
    add_collection_item,
    get_meeting as get_meeting_raw,
    get_meeting_enriched as get_meeting,
    list_meetings_enriched as list_meetings,
    rebuild_meeting_view,
    schedule_meeting,
    update_collection_item,
    update_meeting_field,
)
from src.governance.mrc.pack import render_pack_pdf
from src.governance.mrc_settings import get_settings
from src.web._helpers import context_from_request, json_body, request_actor
from src.web._signoff_routing import drain_pending_for_meeting
from src.web.api_mrc._bp import mrc_bp


def _in_scope_item(meeting: dict, model_id: str) -> dict | None:
    return next((i for i in (meeting["data"].get("models_in_scope") or [])
                 if i.get("model_id") == model_id), None)


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


@mrc_bp.get("/<meeting_id>/models")
def models_in_scope(meeting_id: str):
    """In-scope models joined to the inventory, with derived review status."""
    meeting = get_meeting(meeting_id)
    if meeting is None:
        return jsonify({"error": "meeting not found"}), 404
    today = date.today().isoformat()
    rows = []
    for item in meeting["data"].get("models_in_scope") or []:
        model = get_model(item.get("model_id"))
        data = model["data"] if model else {}
        rows.append({
            "item_id": item.get("item_id"),
            "model_id": item.get("model_id"),
            "name": data.get("name"),
            "tier": data.get("tier"),
            "rag_rating": data.get("rag_rating"),
            "review_status": compute_review_status(data.get("next_review_date"), today),
            "presenter": item.get("presenter"),
            "analysis_original_name": item.get("analysis_original_name"),
        })
    return jsonify(rows)


@mrc_bp.post("/<meeting_id>/models/<model_id>/analysis")
def upload_model_analysis(meeting_id: str, model_id: str):
    """Upload the analysis document for an in-scope model at this meeting."""
    meeting = get_meeting_raw(meeting_id)
    if meeting is None:
        return jsonify({"error": "meeting not found"}), 404
    item = _in_scope_item(meeting, model_id)
    if item is None:
        return jsonify({"error": "model is not in scope for this meeting"}), 400
    file = request.files.get("file")
    if file is None:
        return jsonify({"error": "no file provided"}), 400
    try:
        meta = save_upload("meeting_analysis", file.filename, file.read())
    except UploadError as exc:
        return jsonify({"error": str(exc)}), 400
    update_collection_item(
        meeting_id=meeting_id, collection="models_in_scope", item_id=item["item_id"],
        fields={"analysis_filename": meta["filename"], "analysis_original_name": meta["original_name"]},
        actor=request_actor(),
    )
    rebuild_meeting_view()
    return jsonify(get_meeting(meeting_id)), 201


@mrc_bp.get("/<meeting_id>/models/<model_id>/analysis")
def download_model_analysis(meeting_id: str, model_id: str):
    """Download a model's analysis document for this meeting, if uploaded."""
    meeting = get_meeting_raw(meeting_id)
    item = _in_scope_item(meeting, model_id) if meeting else None
    if item is None or not item.get("analysis_filename"):
        return jsonify({"error": "no analysis uploaded"}), 404
    path = upload_path("meeting_analysis", item["analysis_filename"])
    if not path.exists():
        return jsonify({"error": "analysis file missing"}), 404
    return send_file(str(path), as_attachment=True,
                     download_name=item.get("analysis_original_name") or "analysis")


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
    # Seed the standard high-level agenda. The detail of model sign-offs and
    # analysis lives in the Models tab, so the agenda stays a running order.
    for title, desc in _DEFAULT_AGENDA:
        dispatch(
            "add_collection_item", add_collection_item, context=ctx,
            meeting_id=meeting_id, collection="agenda",
            fields={"title": title, "description": desc},
        )
    rebuild_meeting_view()
    # Pull any queued sign-off requests for this committee onto the new agenda.
    # (They carry the subject id + proposed RAG but render in the Models tab.)
    drain_pending_for_meeting(ctx, get_meeting_raw(meeting_id) or {"meeting_id": meeting_id, "data": {}})
    return jsonify(get_meeting(meeting_id)), 201


# The standing MRC agenda seeded on every new meeting.
_DEFAULT_AGENDA = (
    ("Rollcall and Confirmation of Quorum",
     "Confirm attendance in the participants panel; the meeting may proceed only once quorate."),
    ("Sign-off of the previous MRM minutes",
     "Proposed by the chair."),
    ("Review model sign-off",
     "Risk-rating sign-offs are reviewed in the Models tab (Approvals)."),
    ("Review model analysis",
     "Model analyses are reviewed in the Models tab (Analysis) — confirmation to proceed and any actions."),
    ("Any Other Business (AOB)", ""),
)


@mrc_bp.post("/<meeting_id>/field")
def update_field(meeting_id: str):
    body = json_body()
    dispatch(
        "update_meeting_field", update_meeting_field, context=context_from_request(body),
        meeting_id=meeting_id, field=body.get("field"), value=body.get("value"),
    )
    rebuild_meeting_view()
    return jsonify(get_meeting(meeting_id))
