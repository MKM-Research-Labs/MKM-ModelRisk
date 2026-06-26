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
"""HTTP API for the MRC-meeting aggregate."""
from __future__ import annotations

from datetime import date

from flask import Blueprint, Response, jsonify

from config.governance import MEETING_FIELD_SPECS, MRC_COLLECTION_SPECS
from src.command import dispatch
from src.governance.model_inventory import get_model
from src.governance.model_inventory.review import compute_review_status
from src.governance.mrc.pack import render_pack_pdf
from src.governance.mrc_settings import get_settings
from src.governance.mrc import (
    add_collection_item,
    get_meeting,
    list_meetings,
    rebuild_meeting_view,
    remove_collection_item,
    schedule_meeting,
    update_collection_item,
    update_meeting_field,
)
from src.web._helpers import context_from_request, json_body, reference_options, resolve_field

mrc_bp = Blueprint("mrc", __name__, url_prefix="/api/meetings")


def _field_specs():
    options_by_list = reference_options()
    return [resolve_field({**spec, "key": key}, options_by_list)
            for key, spec in MEETING_FIELD_SPECS.items()]


def _collection_specs():
    options_by_list = reference_options()
    return [
        {
            "key": key, "label": spec["label"], "id_prefix": spec["id_prefix"],
            "fields": [resolve_field(f, options_by_list) for f in spec["fields"]],
        }
        for key, spec in MRC_COLLECTION_SPECS.items()
    ]


@mrc_bp.get("/fields")
def field_specs():
    return jsonify({"fields": _field_specs(), "collections": _collection_specs()})


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
        })
    return jsonify(rows)


@mrc_bp.post("")
def schedule():
    body = json_body()
    meeting_id = body.get("meeting_id")
    dispatch(
        "schedule_meeting", schedule_meeting, context=context_from_request(body),
        meeting_id=meeting_id, title=body.get("title"), date=body.get("date"),
        fields=body.get("fields") or {},
    )
    rebuild_meeting_view()
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


@mrc_bp.post("/<meeting_id>/collections/<collection>")
def add_item(meeting_id: str, collection: str):
    body = json_body()
    dispatch(
        "add_collection_item", add_collection_item, context=context_from_request(body),
        meeting_id=meeting_id, collection=collection, fields=body.get("fields") or {},
    )
    rebuild_meeting_view()
    return jsonify(get_meeting(meeting_id)), 201


@mrc_bp.post("/<meeting_id>/collections/<collection>/bulk")
def add_items_bulk(meeting_id: str, collection: str):
    """Add up to N items to a collection in one submission.

    Items with all-empty fields are skipped so the UI can submit a fixed
    number of input rows and only commit the populated ones. Each accepted
    item becomes its own event (preserving event-log granularity).
    """
    body = json_body()
    ctx = context_from_request(body)
    for item in body.get("items") or []:
        fields = (item.get("fields") if isinstance(item, dict) else None) or {}
        if not any(str(v).strip() for v in fields.values()):
            continue
        dispatch(
            "add_collection_item", add_collection_item, context=ctx,
            meeting_id=meeting_id, collection=collection, fields=fields,
        )
    rebuild_meeting_view()
    return jsonify(get_meeting(meeting_id)), 201


@mrc_bp.post("/<meeting_id>/collections/models_in_scope/set")
def set_models_in_scope(meeting_id: str):
    """Replace the in-scope model set with the given list.

    The diff is computed against the current state: new ids are added,
    missing ids are removed. Each add/remove is still a separate event,
    so the audit trail records exactly what changed.
    """
    body = json_body()
    ctx = context_from_request(body)
    desired = {mid for mid in (body.get("model_ids") or []) if mid}
    meeting = get_meeting(meeting_id)
    if meeting is None:
        return jsonify({"error": "meeting not found"}), 404
    current_items = meeting["data"].get("models_in_scope") or []
    current_by_id = {it["model_id"]: it["item_id"] for it in current_items if it.get("model_id")}
    for model_id in desired - current_by_id.keys():
        dispatch(
            "add_collection_item", add_collection_item, context=ctx,
            meeting_id=meeting_id, collection="models_in_scope",
            fields={"model_id": model_id},
        )
    for model_id in current_by_id.keys() - desired:
        dispatch(
            "remove_collection_item", remove_collection_item, context=ctx,
            meeting_id=meeting_id, collection="models_in_scope",
            item_id=current_by_id[model_id],
        )
    rebuild_meeting_view()
    return jsonify(get_meeting(meeting_id))


@mrc_bp.post("/<meeting_id>/collections/<collection>/<item_id>")
def update_item(meeting_id: str, collection: str, item_id: str):
    body = json_body()
    dispatch(
        "update_collection_item", update_collection_item, context=context_from_request(body),
        meeting_id=meeting_id, collection=collection, item_id=item_id,
        fields=body.get("fields") or {},
    )
    rebuild_meeting_view()
    return jsonify(get_meeting(meeting_id))


@mrc_bp.post("/<meeting_id>/collections/<collection>/<item_id>/delete")
def delete_item(meeting_id: str, collection: str, item_id: str):
    body = json_body()
    dispatch(
        "remove_collection_item", remove_collection_item, context=context_from_request(body),
        meeting_id=meeting_id, collection=collection, item_id=item_id,
    )
    rebuild_meeting_view()
    return jsonify(get_meeting(meeting_id))

