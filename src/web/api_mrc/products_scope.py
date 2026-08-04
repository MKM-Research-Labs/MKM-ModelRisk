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
"""Products-in-scope for a meeting: the exact mirror of the models-in-scope
endpoints (set / join / analysis document), so the Signoff tab's Analysis
section can cover products alongside models."""
from __future__ import annotations

from datetime import date

from flask import jsonify, request, send_file

from src.command import dispatch
from src.files import UploadError, save_upload, upload_path
from src.governance.model_inventory.review import compute_review_status
from src.governance.mrc import (
    add_collection_item,
    get_meeting as get_meeting_raw,
    get_meeting_enriched as get_meeting,
    rebuild_meeting_view,
    remove_collection_item,
    update_collection_item,
)
from src.governance.product import get_product
from src.web._helpers import context_from_request, json_body, request_actor
from src.web.api_mrc._bp import mrc_bp


def _in_scope_product(meeting: dict, product_id: str) -> dict | None:
    return next((i for i in (meeting["data"].get("products_in_scope") or [])
                 if i.get("product_id") == product_id), None)


@mrc_bp.post("/<meeting_id>/collections/products_in_scope/set")
def set_products_in_scope(meeting_id: str):
    """Replace the in-scope product set with the given list (diffed to events)."""
    body = json_body()
    ctx = context_from_request(body)
    desired = {pid for pid in (body.get("product_ids") or []) if pid}
    meeting = get_meeting(meeting_id)
    if meeting is None:
        return jsonify({"error": "meeting not found"}), 404
    current = meeting["data"].get("products_in_scope") or []
    current_by_id = {it["product_id"]: it["item_id"] for it in current if it.get("product_id")}
    for product_id in desired - current_by_id.keys():
        dispatch("add_collection_item", add_collection_item, context=ctx,
                 meeting_id=meeting_id, collection="products_in_scope",
                 fields={"product_id": product_id})
    for product_id in current_by_id.keys() - desired:
        dispatch("remove_collection_item", remove_collection_item, context=ctx,
                 meeting_id=meeting_id, collection="products_in_scope",
                 item_id=current_by_id[product_id])
    rebuild_meeting_view()
    return jsonify(get_meeting(meeting_id))


@mrc_bp.get("/<meeting_id>/products")
def products_in_scope(meeting_id: str):
    """In-scope products joined to the register, with derived review status."""
    meeting = get_meeting(meeting_id)
    if meeting is None:
        return jsonify({"error": "meeting not found"}), 404
    today = date.today().isoformat()
    rows = []
    for item in meeting["data"].get("products_in_scope") or []:
        product = get_product(item.get("product_id"))
        data = product["data"] if product else {}
        rows.append({
            "item_id": item.get("item_id"),
            "product_id": item.get("product_id"),
            "name": data.get("product"),
            "tier": data.get("tier"),
            "rag_rating": data.get("rag_rating"),
            "review_status": compute_review_status(data.get("next_review_date"), today),
            "presenter": item.get("presenter"),
            "analysis_status": item.get("analysis_status"),
            "analysis_note": item.get("analysis_note"),
            "proceed_basis": item.get("proceed_basis"),
            "analysis_filename": item.get("analysis_filename"),
            "analysis_original_name": item.get("analysis_original_name"),
        })
    return jsonify(rows)


@mrc_bp.post("/<meeting_id>/products/<product_id>/analysis")
def upload_product_analysis(meeting_id: str, product_id: str):
    """Upload the analysis document for an in-scope product at this meeting."""
    meeting = get_meeting_raw(meeting_id)
    if meeting is None:
        return jsonify({"error": "meeting not found"}), 404
    item = _in_scope_product(meeting, product_id)
    if item is None:
        return jsonify({"error": "product is not in scope for this meeting"}), 400
    file = request.files.get("file")
    if file is None:
        return jsonify({"error": "no file provided"}), 400
    try:
        meta = save_upload("meeting_analysis", file.filename, file.read())
    except UploadError as exc:
        return jsonify({"error": str(exc)}), 400
    update_collection_item(
        meeting_id=meeting_id, collection="products_in_scope", item_id=item["item_id"],
        fields={"analysis_filename": meta["filename"], "analysis_original_name": meta["original_name"]},
        actor=request_actor())
    rebuild_meeting_view()
    return jsonify(get_meeting(meeting_id)), 201


@mrc_bp.get("/<meeting_id>/products/<product_id>/analysis")
def download_product_analysis(meeting_id: str, product_id: str):
    """Download a product's analysis document for this meeting, if uploaded."""
    meeting = get_meeting_raw(meeting_id)
    item = _in_scope_product(meeting, product_id) if meeting else None
    if item is None or not item.get("analysis_filename"):
        return jsonify({"error": "no analysis uploaded"}), 404
    path = upload_path("meeting_analysis", item["analysis_filename"])
    if not path.exists():
        return jsonify({"error": "analysis file missing"}), 404
    return send_file(str(path), as_attachment=True,
                     download_name=item.get("analysis_original_name") or "analysis")


@mrc_bp.post("/<meeting_id>/products/<product_id>/analysis/remove")
def remove_product_analysis(meeting_id: str, product_id: str):
    """Detach the uploaded analysis from an in-scope product at this meeting."""
    meeting = get_meeting_raw(meeting_id)
    if meeting is None:
        return jsonify({"error": "meeting not found"}), 404
    item = _in_scope_product(meeting, product_id)
    if item is None:
        return jsonify({"error": "product is not in scope for this meeting"}), 400
    update_collection_item(
        meeting_id=meeting_id, collection="products_in_scope", item_id=item["item_id"],
        fields={"analysis_filename": "", "analysis_original_name": ""}, actor=request_actor(),
    )
    rebuild_meeting_view()
    return jsonify(get_meeting(meeting_id)), 200
