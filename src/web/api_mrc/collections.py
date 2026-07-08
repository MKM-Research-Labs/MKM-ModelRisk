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
"""Meeting collection endpoints: add / bulk-add / update / delete + the
models-in-scope set-diff. Attached to the shared ``mrc_bp``."""
from __future__ import annotations

from flask import jsonify

from src.command import dispatch
from src.governance.mrc import (
    add_collection_item,
    get_meeting_enriched as get_meeting,
    rebuild_meeting_view,
    remove_collection_item,
    update_collection_item,
)
from src.web._helpers import context_from_request, json_body
from src.web.api_mrc._bp import mrc_bp


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
