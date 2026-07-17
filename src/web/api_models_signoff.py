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

from datetime import date

from src.governance.model_inventory import get_model
from src.governance.model_inventory.risk import compute_risk_rating
from src.governance.mrc import get_meeting, matching_mrc
from src.governance.reference import get_reference_lists
from src.command import require_confirmation
from src.web._helpers import context_from_request, json_body
from src.web._signoff_routing import MODEL_SUBJECT, REQUESTS, _newest, raise_signoff, revoke_signoff
from src.web.api_models import models_bp


def pending_signoff(model_id: str) -> dict | None:
    """The model's current active (Pending or Attached) sign-off request, if any.

    Reads the model-side queue (the source of truth). For an Attached request it
    resolves the meeting it landed on so the UI can link back.
    """
    model = get_model(model_id)
    requests = (model["data"].get(REQUESTS) or []) if model else []
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
    ctx = context_from_request(body)
    raise_signoff(ctx, MODEL_SUBJECT, model_id,
                  proposed_rag=proposed_rag, target_mrc=mrc["value"], note=body.get("note"))
    return jsonify(get_model(model_id)), 201


@models_bp.post("/<model_id>/revoke-signoff")
def revoke_model_signoff(model_id: str):
    """Revoke a granted MRC sign-off — the rating is kept but no longer approved,
    so the model returns to needing sign-off. Records a Revoked history entry."""
    model = get_model(model_id)
    if model is None:
        return jsonify({"error": "model not found"}), 404
    risk = compute_risk_rating(model["data"] or {}, as_of=date.today().isoformat())
    if not risk.get("signed_off"):
        return jsonify({"error": "model is not currently signed off"}), 400
    body = json_body()
    ctx = context_from_request(body)
    require_confirmation("revoke_signoff", ctx)
    revoke_signoff(ctx, MODEL_SUBJECT, model_id, note=body.get("note") or body.get("reason"))
    return jsonify(get_model(model_id))
