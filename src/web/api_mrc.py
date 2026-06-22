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

from flask import Blueprint, jsonify

from src.command import dispatch
from src.governance.mrc import (
    add_agenda_item,
    get_meeting,
    list_meetings,
    log_decision,
    raise_action,
    rebuild_meeting_view,
    schedule_meeting,
    set_action_status,
    update_meeting_field,
)
from src.web._helpers import context_from_request, json_body

mrc_bp = Blueprint("mrc", __name__, url_prefix="/api/meetings")


def _run(command_name, handler, meeting_id, body, **kwargs):
    dispatch(
        command_name, handler, context=context_from_request(body),
        meeting_id=meeting_id, **kwargs,
    )
    rebuild_meeting_view()
    return jsonify(get_meeting(meeting_id))


@mrc_bp.get("")
def list_all():
    return jsonify(list_meetings())


@mrc_bp.get("/<meeting_id>")
def get_one(meeting_id: str):
    meeting = get_meeting(meeting_id)
    if meeting is None:
        return jsonify({"error": "meeting not found"}), 404
    return jsonify(meeting)


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
    return _run(
        "update_meeting_field", update_meeting_field, meeting_id, body,
        field=body.get("field"), value=body.get("value"),
    )


@mrc_bp.post("/<meeting_id>/agenda")
def add_agenda(meeting_id: str):
    body = json_body()
    return _run(
        "add_agenda_item", add_agenda_item, meeting_id, body,
        title=body.get("title"), presenter=body.get("presenter"),
    )


@mrc_bp.post("/<meeting_id>/decisions")
def add_decision(meeting_id: str):
    body = json_body()
    return _run("log_decision", log_decision, meeting_id, body, text=body.get("text"))


@mrc_bp.post("/<meeting_id>/actions")
def add_action(meeting_id: str):
    body = json_body()
    return _run(
        "raise_action", raise_action, meeting_id, body,
        description=body.get("description"), owner=body.get("owner"),
        due_date=body.get("due_date"),
    )


@mrc_bp.post("/<meeting_id>/actions/<action_id>/status")
def set_status(meeting_id: str, action_id: str):
    body = json_body()
    return _run(
        "set_action_status", set_action_status, meeting_id, body,
        action_id=action_id, status=body.get("status"),
    )
