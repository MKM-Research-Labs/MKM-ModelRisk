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

"""MRC meeting agenda CRUD routes."""

from flask import jsonify, request

from . import governance_bp
from ._helpers import _find_meeting, _save_and_respond


@governance_bp.route("/governance/mrc/meetings/<meeting_id>/agenda", methods=["POST"])
def add_agenda_item(meeting_id):
    """Add an agenda item to a meeting."""
    meetings, meeting, err = _find_meeting(meeting_id)
    if err:
        return err, 404

    data = request.get_json(silent=True) or {}
    agenda = meeting.setdefault("agenda", [])

    item_num = len(agenda) + 1
    agenda.append({
        "item": item_num,
        "title": data.get("title", ""),
        "description": data.get("description", ""),
        "presenter": data.get("presenter", ""),
        "duration": data.get("duration", ""),
        "status": data.get("status", "Pending"),
    })

    return _save_and_respond(meetings, meeting)


@governance_bp.route("/governance/mrc/meetings/<meeting_id>/agenda/<int:item_num>/update", methods=["POST"])
def update_agenda_item(meeting_id, item_num):
    """Update an agenda item."""
    meetings, meeting, err = _find_meeting(meeting_id)
    if err:
        return err, 404

    agenda = meeting.get("agenda", [])
    item = next((a for a in agenda if a.get("item") == item_num), None)
    if not item:
        return jsonify({"status": "error", "message": f"Agenda item {item_num} not found"}), 404

    data = request.get_json(silent=True) or {}
    for field in ["title", "description", "presenter", "duration", "status"]:
        if field in data:
            item[field] = data[field]

    return _save_and_respond(meetings, meeting)


@governance_bp.route("/governance/mrc/meetings/<meeting_id>/agenda/<int:item_num>/delete", methods=["POST"])
def delete_agenda_item(meeting_id, item_num):
    """Delete an agenda item and renumber remaining items."""
    meetings, meeting, err = _find_meeting(meeting_id)
    if err:
        return err, 404

    agenda = meeting.get("agenda", [])
    meeting["agenda"] = [a for a in agenda if a.get("item") != item_num]
    # Renumber
    for i, a in enumerate(meeting["agenda"], 1):
        a["item"] = i

    return _save_and_respond(meetings, meeting)
