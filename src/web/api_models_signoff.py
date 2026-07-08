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

The owner-side of the workflow: queue a Risk Rating sign-off as an agenda item
against a Scheduled MRC meeting. The meeting-side (approve-signoff) lives in
``api_mrc``. Registered on the shared ``models_bp`` blueprint.
"""
from __future__ import annotations

from flask import jsonify

from src.command import dispatch
from src.governance.model_inventory import get_model
from src.governance.mrc import add_collection_item as _mrc_add
from src.governance.mrc import get_meeting, meeting_items_for_model, rebuild_meeting_view
from src.web._helpers import context_from_request, json_body
from src.web.api_models import models_bp


def pending_signoff(model_id: str) -> dict | None:
    """The oldest unapproved sign-off agenda item pointing at this model, if any."""
    for item in meeting_items_for_model("agenda", model_id, field="subject_model_id"):
        if item.get("proposed_rag") and item.get("status") == "Pending":
            return {
                "meeting_id": item["meeting_id"],
                "meeting_title": item.get("meeting_title"),
                "meeting_date": item.get("meeting_date"),
                "agenda_item_id": item["item_id"],
                "proposed_rag": item["proposed_rag"],
            }
    return None


@models_bp.post("/<model_id>/request-signoff")
def request_signoff(model_id: str):
    """Owner queues an MRC sign-off request — spawns an agenda item on the
    chosen Scheduled meeting, tagged with subject_model_id + proposed_rag."""
    if get_model(model_id) is None:
        return jsonify({"error": "model not found"}), 404
    body = json_body()
    meeting_id = body.get("meeting_id")
    proposed_rag = body.get("proposed_rag")
    if not meeting_id or not proposed_rag:
        return jsonify({"error": "meeting_id and proposed_rag are required"}), 400
    meeting = get_meeting(meeting_id)
    if meeting is None:
        return jsonify({"error": "meeting not found"}), 404
    if meeting["status"] != "Scheduled":
        return jsonify({"error": "sign-off can only be requested against a Scheduled meeting"}), 400
    dispatch(
        "add_collection_item", _mrc_add, context=context_from_request(body),
        meeting_id=meeting_id, collection="agenda",
        fields={
            "title": f"Risk rating sign-off: {model_id} → {proposed_rag}",
            "subject_model_id": model_id,
            "proposed_rag": proposed_rag,
            "status": "Pending",
        },
    )
    rebuild_meeting_view()
    return jsonify(get_model(model_id)), 201
