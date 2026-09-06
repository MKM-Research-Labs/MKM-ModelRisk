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
