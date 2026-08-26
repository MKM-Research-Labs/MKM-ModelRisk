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
"""The models in scope at a meeting, and the analysis presented for each.

The model half of what a committee reviews; ``products_scope`` is the other. Split
out of ``lifecycle`` when that file passed R2's 300-line limit -- and split HERE
because this is where it already divided: lifecycle is what happens to a meeting
(scheduled, agenda locked, packed, closed), and this is what the meeting is about.

Attached to the shared ``mrc_bp``, so the URL space is unchanged.
"""
from __future__ import annotations

from datetime import date

from flask import jsonify, request, send_file

from src.files import UploadError, save_upload, upload_path
from src.governance.documents import add_document, model_scope
from src.governance.model_inventory import get_model, rebuild_inventory_view
from src.governance.model_inventory.commands import AGGREGATE_TYPE as MODEL_AGGREGATE
from src.governance.model_inventory.review import compute_review_status
from src.governance.mrc import (
    get_meeting as get_meeting_raw,
    get_meeting_enriched as get_meeting,
    rebuild_meeting_view,
    update_collection_item,
)
from src.web._helpers import request_actor
from src.web.api_mrc._bp import mrc_bp


def _in_scope_item(meeting: dict, model_id: str) -> dict | None:
    return next((i for i in (meeting["data"].get("models_in_scope") or [])
                 if i.get("model_id") == model_id), None)


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
            # The committee's recorded outcome + discussion note for this model.
            # Without these the Analysis panel always re-renders the Outcome as
            # "Pending" and a blank note, so saved values never appear to stick.
            "analysis_status": item.get("analysis_status"),
            "analysis_note": item.get("analysis_note"),
            "proceed_basis": item.get("proceed_basis"),
            # Carry the uploaded-analysis filename so the review panel can show the
            # download link (its presence check) and the recorded basis to proceed.
            "analysis_filename": item.get("analysis_filename"),
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
    data = file.read()
    try:
        meta = save_upload("meeting_analysis", file.filename, data)
    except UploadError as exc:
        return jsonify({"error": str(exc)}), 400
    update_collection_item(
        meeting_id=meeting_id, collection="models_in_scope", item_id=item["item_id"],
        fields={"analysis_filename": meta["filename"], "analysis_original_name": meta["original_name"]},
        actor=request_actor(),
    )
    # File the presented analysis on the model itself, under Docs / Analysis, so it
    # lives with the model's record and shows on its Docs tab — not only on the
    # meeting. The meeting keeps its own reference (analysis_filename) above.
    add_document(
        aggregate_type=MODEL_AGGREGATE, aggregate_id=model_id, scope=model_scope(model_id),
        category="Analysis", filename=meta["original_name"] or file.filename, data=data,
        description=f"Analysis presented to the MRC at {meeting_id}", actor=request_actor(),
    )
    rebuild_inventory_view()
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


@mrc_bp.post("/<meeting_id>/models/<model_id>/analysis/remove")
def remove_model_analysis(meeting_id: str, model_id: str):
    """Detach the uploaded analysis from an in-scope model at this meeting. The copy
    filed on the model (Docs / Analysis) is left in place — it is the model's record."""
    meeting = get_meeting_raw(meeting_id)
    if meeting is None:
        return jsonify({"error": "meeting not found"}), 404
    item = _in_scope_item(meeting, model_id)
    if item is None:
        return jsonify({"error": "model is not in scope for this meeting"}), 400
    update_collection_item(
        meeting_id=meeting_id, collection="models_in_scope", item_id=item["item_id"],
        fields={"analysis_filename": "", "analysis_original_name": ""}, actor=request_actor(),
    )
    rebuild_meeting_view()
    return jsonify(get_meeting(meeting_id)), 200
