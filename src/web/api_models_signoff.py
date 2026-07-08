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
"""W4c — Risk rating sign-off request endpoint.

The owner-side of the workflow: a request is routed to the model's responsible
MRC (derived from its division/department) and queued on the model. If a meeting
of that committee is already Scheduled it is attached at once; otherwise it waits
as Pending and is drained onto the agenda when such a meeting is scheduled (see
``api_mrc.lifecycle``). The meeting-side (approve-signoff) lives in ``api_mrc``.
Registered on the shared ``models_bp`` blueprint.
"""
from __future__ import annotations

from flask import jsonify

from src.command import dispatch
from src.governance.model_inventory import (
    add_collection_item as _model_add,
    get_model,
    rebuild_inventory_view,
)
from src.governance.mrc import get_meeting, matching_mrc
from src.governance.reference import get_reference_lists
from src.web._helpers import context_from_request, json_body
from src.web._signoff_routing import _newest, attach_request, earliest_scheduled_for_mrc
from src.web.api_models import models_bp


def pending_signoff(model_id: str) -> dict | None:
    """The model's current active (Pending or Attached) sign-off request, if any.

    Reads the model-side queue (the source of truth). For an Attached request it
    resolves the meeting it landed on so the UI can link back.
    """
    model = get_model(model_id)
    requests = (model["data"].get("rag_signoff_requests") or []) if model else []
    active = [r for r in requests if r.get("status") in ("Pending", "Attached")]
    request = _newest(active)
    if request is None:
        return None
    result = {
        "proposed_rag": request.get("proposed_rag"),
        "target_mrc": request.get("target_mrc"),
        "status": request.get("status"),
    }
    if request.get("status") == "Attached" and request.get("meeting_id"):
        meeting = get_meeting(request["meeting_id"])
        data = (meeting["data"] if meeting else {}) or {}
        result.update({
            "meeting_id": request["meeting_id"],
            "meeting_title": data.get("title"),
            "meeting_date": data.get("date"),
            "agenda_item_id": request.get("agenda_item_id"),
        })
    return result


@models_bp.post("/<model_id>/request-signoff")
def request_signoff(model_id: str):
    """Owner raises an MRC sign-off request. It is routed to the model's
    responsible MRC and queued; attached immediately if a meeting is Scheduled,
    else left Pending for the next meeting of that committee to pick up."""
    model = get_model(model_id)
    if model is None:
        return jsonify({"error": "model not found"}), 404
    body = json_body()
    proposed_rag = body.get("proposed_rag")
    if not proposed_rag:
        return jsonify({"error": "proposed_rag is required"}), 400
    data = model["data"] or {}
    mrc, _level = matching_mrc(data.get("division"), data.get("department"), get_reference_lists())
    if mrc is None:
        return jsonify({"error": "no MRC committee covers this model's division/department — "
                                 "configure one under Admin → MRC first"}), 400
    target_mrc = mrc["value"]
    ctx = context_from_request(body)
    fields = {"proposed_rag": proposed_rag, "target_mrc": target_mrc, "status": "Pending"}
    if body.get("note"):
        fields["note"] = body["note"]
    dispatch(
        "add_collection_item", _model_add, context=ctx,
        model_id=model_id, collection="rag_signoff_requests", fields=fields,
    )
    rebuild_inventory_view()
    # Attach straight away if the committee already has a Scheduled meeting.
    refreshed = get_model(model_id)
    request = _newest(refreshed["data"].get("rag_signoff_requests") or [])
    meeting = earliest_scheduled_for_mrc(target_mrc)
    if meeting is not None and request is not None:
        attach_request(ctx, model_id, request, meeting)
    return jsonify(get_model(model_id)), 201
