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
"""The MRC receiving an operational event (W4b RACI feed-up).

Product events are allocated onto a meeting's agenda when it is scheduled (see
``_event_review``). Here the committee formally *receives* one: it stamps the event
Received with the committee's comments, records any action items from the minuted
discussion onto the product, minutes the decision, and completes the agenda item —
all under one confirmation.
"""
from __future__ import annotations

from flask import jsonify

from src.command import dispatch, require_confirmation
from src.governance.mrc import (
    add_collection_item,
    get_meeting_enriched as get_meeting,
    rebuild_meeting_view,
    update_collection_item,
)
from src.governance.product import (
    add_collection_item as product_add,
    get_product,
    rebuild_product_view,
    update_collection_item as product_update,
)
from src.web._helpers import context_from_request, json_body
from src.web.api_mrc._bp import mrc_bp
from src.web.api_mrc._quorum import is_quorate

EVENTS = "operational_failure_events"


@mrc_bp.post("/<meeting_id>/agenda/<item_id>/receive-event")
def receive_event(meeting_id: str, item_id: str):
    """The committee receives the product event named by an event-review agenda item."""
    body = json_body()
    meeting = get_meeting(meeting_id)
    if meeting is None:
        return jsonify({"error": "meeting not found"}), 404
    item = next((a for a in (meeting["data"].get("agenda") or [])
                 if a.get("item_id") == item_id), None)
    if item is None:
        return jsonify({"error": "agenda item not found"}), 404
    product_id = item.get("subject_product_id")
    event_id = item.get("subject_event_id")
    if not product_id or not event_id:
        return jsonify({"error": "agenda item is not an event review"}), 400
    # The product is guaranteed to exist — the item was allocated from its event,
    # and products are retired, never deleted.
    # A committee decision only stands once the meeting is quorate — the same gate
    # as a sign-off decision.
    if not is_quorate(meeting["data"]):
        return jsonify({"error": "meeting is not quorate"}), 400
    ctx = context_from_request(body)
    # Composed op (several sub-commands) — gate it once before anything mutates.
    require_confirmation("receive_event", ctx)
    comments = body.get("comments") or body.get("reason") or ""

    # 1. Stamp the event Received on the product.
    dispatch("update_collection_item", product_update, context=ctx,
             product_id=product_id, collection=EVENTS, item_id=event_id,
             fields={"mrc_status": "Received", "review_comments": comments,
                     "mrc_meeting": meeting_id})
    # 2. Record any action items from the minuted discussion onto the product.
    for action in body.get("actions") or []:
        description = (action or {}).get("description")
        if not description:
            continue
        dispatch("add_collection_item", product_add, context=ctx,
                 product_id=product_id, collection="actions",
                 fields={"description": description, "owner": action.get("owner", ""),
                         "target_date": action.get("target_date", ""), "status": "Open",
                         "raised_meeting": meeting_id})
    # 3. Minute the decision.
    text = f"MRC received the operational event on {product_id}."
    if comments:
        text += " " + comments
    dispatch("add_collection_item", add_collection_item, context=ctx,
             meeting_id=meeting_id, collection="minutes",
             fields={"title": f"Event received — {product_id}", "product_id": product_id,
                     "text": text, "agenda_item_id": item_id})
    # 4. Complete the agenda item.
    dispatch("update_collection_item", update_collection_item, context=ctx,
             meeting_id=meeting_id, collection="agenda", item_id=item_id,
             fields={"status": "Completed"})
    rebuild_meeting_view()
    rebuild_product_view()
    return jsonify({"meeting": get_meeting(meeting_id), "product": get_product(product_id)})
