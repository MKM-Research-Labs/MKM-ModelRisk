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

"""MRC meeting decisions CRUD routes."""

from datetime import datetime

from flask import jsonify, request

from . import governance_bp
from ._helpers import _find_meeting, _save_and_respond


@governance_bp.route("/governance/mrc/meetings/<meeting_id>/decisions", methods=["POST"])
def add_decision(meeting_id):
    """Add a decision to a meeting."""
    meetings, meeting, err = _find_meeting(meeting_id)
    if err:
        return err, 404

    data = request.get_json(silent=True) or {}
    decisions = meeting.setdefault("decisions", [])

    # Auto-generate ID: D-NNN
    existing_nums = []
    for d in decisions:
        try:
            existing_nums.append(int(d["id"].split("-")[1]))
        except (IndexError, ValueError):
            pass
    next_num = max(existing_nums, default=0) + 1

    decisions.append({
        "id": f"D-{next_num:03d}",
        "description": data.get("description", ""),
        "date": data.get("date", meeting.get("date", datetime.now().strftime("%Y-%m-%d"))),
    })

    return _save_and_respond(meetings, meeting)


@governance_bp.route("/governance/mrc/meetings/<meeting_id>/decisions/<decision_id>/update", methods=["POST"])
def update_decision(meeting_id, decision_id):
    """Update a decision."""
    meetings, meeting, err = _find_meeting(meeting_id)
    if err:
        return err, 404

    decisions = meeting.get("decisions", [])
    decision = next((d for d in decisions if d["id"] == decision_id), None)
    if not decision:
        return jsonify({"status": "error", "message": f"Decision {decision_id} not found"}), 404

    data = request.get_json(silent=True) or {}
    for field in ["description", "date"]:
        if field in data:
            decision[field] = data[field]

    return _save_and_respond(meetings, meeting)


@governance_bp.route("/governance/mrc/meetings/<meeting_id>/decisions/<decision_id>/delete", methods=["POST"])
def delete_decision(meeting_id, decision_id):
    """Delete a decision."""
    meetings, meeting, err = _find_meeting(meeting_id)
    if err:
        return err, 404

    meeting["decisions"] = [d for d in meeting.get("decisions", []) if d["id"] != decision_id]

    return _save_and_respond(meetings, meeting)
