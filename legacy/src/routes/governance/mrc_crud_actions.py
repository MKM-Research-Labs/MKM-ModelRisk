# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""MRC meeting actions and participants CRUD routes."""

from flask import jsonify, request

from . import governance_bp
from ._helpers import _find_meeting, _save_and_respond


# -- Actions CRUD --

@governance_bp.route("/governance/mrc/meetings/<meeting_id>/actions", methods=["POST"])
def add_action(meeting_id):
    """Add an action item to a meeting."""
    meetings, meeting, err = _find_meeting(meeting_id)
    if err:
        return err, 404

    data = request.get_json(silent=True) or {}
    actions = meeting.setdefault("actions", [])

    # Auto-generate ID: A-NNN
    existing_nums = []
    for a in actions:
        try:
            existing_nums.append(int(a["id"].split("-")[1]))
        except (IndexError, ValueError):
            pass
    next_num = max(existing_nums, default=0) + 1

    actions.append({
        "id": f"A-{next_num:03d}",
        "description": data.get("description", ""),
        "owner": data.get("owner", ""),
        "target_date": data.get("target_date", ""),
        "status": data.get("status", "Open"),
    })

    return _save_and_respond(meetings, meeting)


@governance_bp.route("/governance/mrc/meetings/<meeting_id>/actions/<action_id>/update", methods=["POST"])
def update_action(meeting_id, action_id):
    """Update an action item (including status toggle)."""
    meetings, meeting, err = _find_meeting(meeting_id)
    if err:
        return err, 404

    actions = meeting.get("actions", [])
    action = next((a for a in actions if a["id"] == action_id), None)
    if not action:
        return jsonify({"status": "error", "message": f"Action {action_id} not found"}), 404

    data = request.get_json(silent=True) or {}
    for field in ["description", "owner", "target_date", "status"]:
        if field in data:
            action[field] = data[field]

    return _save_and_respond(meetings, meeting)


@governance_bp.route("/governance/mrc/meetings/<meeting_id>/actions/<action_id>/delete", methods=["POST"])
def delete_action(meeting_id, action_id):
    """Delete an action item."""
    meetings, meeting, err = _find_meeting(meeting_id)
    if err:
        return err, 404

    meeting["actions"] = [a for a in meeting.get("actions", []) if a["id"] != action_id]

    return _save_and_respond(meetings, meeting)


# -- Participants CRUD --

@governance_bp.route("/governance/mrc/meetings/<meeting_id>/participants", methods=["POST"])
def add_participant(meeting_id):
    """Add a participant to a meeting."""
    meetings, meeting, err = _find_meeting(meeting_id)
    if err:
        return err, 404

    data = request.get_json(silent=True) or {}
    participants = meeting.setdefault("participants", [])

    # Auto-generate ID: P-NNN
    existing_nums = []
    for p in participants:
        try:
            existing_nums.append(int(p["id"].split("-")[1]))
        except (IndexError, ValueError):
            pass
    next_num = max(existing_nums, default=0) + 1

    participants.append({
        "id": f"P-{next_num:03d}",
        "name": data.get("name", ""),
        "role": data.get("role", ""),
        "organisation": data.get("organisation", ""),
        "status": data.get("status", "Invited"),
    })

    return _save_and_respond(meetings, meeting)


@governance_bp.route("/governance/mrc/meetings/<meeting_id>/participants/<participant_id>/update", methods=["POST"])
def update_participant(meeting_id, participant_id):
    """Update a participant."""
    meetings, meeting, err = _find_meeting(meeting_id)
    if err:
        return err, 404

    participants = meeting.get("participants", [])
    participant = next((p for p in participants if p["id"] == participant_id), None)
    if not participant:
        return jsonify({"status": "error", "message": f"Participant {participant_id} not found"}), 404

    data = request.get_json(silent=True) or {}
    for field in ["name", "role", "organisation", "status"]:
        if field in data:
            participant[field] = data[field]

    return _save_and_respond(meetings, meeting)


@governance_bp.route("/governance/mrc/meetings/<meeting_id>/participants/<participant_id>/delete", methods=["POST"])
def delete_participant(meeting_id, participant_id):
    """Delete a participant."""
    meetings, meeting, err = _find_meeting(meeting_id)
    if err:
        return err, 404

    meeting["participants"] = [p for p in meeting.get("participants", []) if p["id"] != participant_id]

    return _save_and_respond(meetings, meeting)
