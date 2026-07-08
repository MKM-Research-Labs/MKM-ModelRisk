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

from flask import Response, jsonify

from src.command import dispatch
from src.governance.model_inventory import get_model
from src.governance.model_inventory.review import compute_review_status
from src.governance.mrc import (
    get_meeting as get_meeting_raw,
    get_meeting_enriched as get_meeting,
    list_meetings_enriched as list_meetings,
    rebuild_meeting_view,
    schedule_meeting,
    update_meeting_field,
)
from src.governance.mrc.pack import render_pack_pdf
from src.governance.mrc_settings import get_settings
from src.web._helpers import context_from_request, json_body
from src.web._signoff_routing import drain_pending_for_meeting
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
    ctx = context_from_request(body)
    dispatch(
        "schedule_meeting", schedule_meeting, context=ctx,
        meeting_id=meeting_id, title=body.get("title"), date=body.get("date"),
        fields=body.get("fields") or {},
    )
    rebuild_meeting_view()
    # Pull any queued sign-off requests for this committee onto the new agenda.
    drain_pending_for_meeting(ctx, get_meeting_raw(meeting_id) or {"meeting_id": meeting_id, "data": {}})
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
