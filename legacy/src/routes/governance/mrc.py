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

#
# This software is provided under license by MKM Research Labs.
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

"""MRC meetings routes: list, create, get, update, document upload/serve."""

import os
import uuid
from datetime import datetime

from flask import jsonify, request, send_file
from werkzeug.utils import secure_filename

from . import _constants, governance_bp
from ._constants import ALLOWED_UPLOAD_EXTENSIONS, MAX_UPLOAD_SIZE
from ._helpers import _load_meetings, _save_meetings


@governance_bp.route("/governance/mrc/meetings", methods=["GET"])
def get_mrc_meetings():
    """List all MRC meetings."""
    meetings = _load_meetings()
    # Return summary (without full minutes text to keep payload small)
    summary = []
    for m in meetings:
        summary.append({
            "id": m["id"],
            "title": m["title"],
            "date": m["date"],
            "status": m["status"],
            "chair": m.get("chair", ""),
            "models_in_scope": len(m.get("models_in_scope", [])),
            "agenda_items": len(m.get("agenda", [])),
            "has_minutes": bool(m.get("minutes")),
            "documents": len(m.get("documents", [])),
        })
    summary.sort(key=lambda x: x["date"], reverse=True)
    return jsonify({"status": "success", "meetings": summary})


@governance_bp.route("/governance/mrc/meetings", methods=["POST"])
def create_mrc_meeting():
    """Create a new MRC meeting."""
    data = request.get_json(silent=True) or {}

    default_attendees = [
        {"name": "Johnny Mattimore", "role": "Chair"},
        {"name": "David K Kelly", "role": "Model Owner"},
    ]
    attendees = data.get("attendees", default_attendees)

    # Build participants from attendees if not provided
    participants = data.get("participants", [])
    if not participants:
        for i, att in enumerate(attendees, 1):
            participants.append({
                "id": f"P-{i:03d}",
                "name": att.get("name", ""),
                "role": att.get("role", ""),
                "organisation": "MKM Research Labs",
                "status": "Invited",
            })

    meeting = {
        "id": str(uuid.uuid4())[:8],
        "title": data.get("title", "MRC Meeting"),
        "date": data.get("date", datetime.now().strftime("%Y-%m-%d")),
        "time": data.get("time", "10:00"),
        "location": data.get("location", "Virtual"),
        "status": data.get("status", "Scheduled"),
        "chair": data.get("chair", "Johnny Mattimore"),
        "attendees": attendees,
        "participants": participants,
        "models_in_scope": data.get("models_in_scope", []),
        "agenda": data.get("agenda", []),
        "minutes": data.get("minutes", []),
        "decisions": data.get("decisions", []),
        "actions": data.get("actions", []),
        "documents": data.get("documents", []),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }

    meetings = _load_meetings()
    meetings.append(meeting)
    if not _save_meetings(meetings):
        return jsonify({"status": "error", "message": "Failed to save meeting"}), 500

    return jsonify({"status": "success", "meeting": meeting})


@governance_bp.route("/governance/mrc/meetings/<meeting_id>", methods=["GET"])
def get_mrc_meeting(meeting_id):
    """Get full detail for a single MRC meeting."""
    meetings = _load_meetings()
    meeting = next((m for m in meetings if m["id"] == meeting_id), None)
    if not meeting:
        return jsonify({"status": "error", "message": f"Meeting {meeting_id} not found"}), 404
    return jsonify({"status": "success", "meeting": meeting})


@governance_bp.route("/governance/mrc/meetings/<meeting_id>/update", methods=["POST"])
def update_mrc_meeting(meeting_id):
    """Update an MRC meeting's fields."""
    meetings = _load_meetings()
    meeting = next((m for m in meetings if m["id"] == meeting_id), None)
    if not meeting:
        return jsonify({"status": "error", "message": f"Meeting {meeting_id} not found"}), 404

    data = request.get_json(silent=True) or {}

    allowed_fields = [
        "title", "date", "time", "location", "status", "chair",
        "attendees", "participants", "models_in_scope", "agenda",
        "minutes", "decisions", "actions",
    ]
    for field in allowed_fields:
        if field in data:
            meeting[field] = data[field]
    meeting["updated_at"] = datetime.now().isoformat()

    if not _save_meetings(meetings):
        return jsonify({"status": "error", "message": "Failed to save meeting"}), 500

    return jsonify({"status": "success", "meeting": meeting})


@governance_bp.route("/governance/mrc/meetings/<meeting_id>/documents", methods=["POST"])
def upload_meeting_document(meeting_id):
    """Upload a supporting document to a meeting."""
    meetings = _load_meetings()
    meeting = next((m for m in meetings if m["id"] == meeting_id), None)
    if not meeting:
        return jsonify({"status": "error", "message": f"Meeting {meeting_id} not found"}), 404

    if "file" not in request.files:
        return jsonify({"status": "error", "message": "No file provided"}), 400

    f = request.files["file"]
    if not f.filename:
        return jsonify({"status": "error", "message": "No file selected"}), 400

    # Validate file extension
    ext = os.path.splitext(f.filename)[1].lstrip('.').lower()
    if ext not in ALLOWED_UPLOAD_EXTENSIONS:
        return jsonify({"status": "error", "message": f"File type '.{ext}' not allowed"}), 400

    # Validate file size
    f.seek(0, 2)
    size = f.tell()
    f.seek(0)
    if size > MAX_UPLOAD_SIZE:
        return jsonify({"status": "error", "message": "File exceeds 50 MB limit"}), 413

    upload_dir = os.path.join(_constants.MRC_UPLOADS_DIR, meeting_id)
    os.makedirs(upload_dir, exist_ok=True)

    filename = secure_filename(f.filename)
    f.save(os.path.join(upload_dir, filename))

    doc_entry = {
        "filename": filename,
        "original_name": f.filename,
        "uploaded_at": datetime.now().isoformat(),
        "uploaded_by": request.form.get("user", "David K Kelly"),
        "description": request.form.get("description", ""),
    }

    if "documents" not in meeting:
        meeting["documents"] = []
    meeting["documents"].append(doc_entry)
    meeting["updated_at"] = datetime.now().isoformat()

    if not _save_meetings(meetings):
        return jsonify({"status": "error", "message": "Failed to save meeting"}), 500

    return jsonify({"status": "success", "document": doc_entry})


@governance_bp.route("/governance/mrc/meetings/<meeting_id>/documents/<filename>", methods=["GET"])
def get_meeting_document(meeting_id, filename):
    """Serve an uploaded meeting document."""
    safe_name = secure_filename(filename)
    file_path = os.path.join(_constants.MRC_UPLOADS_DIR, meeting_id, safe_name)
    if not os.path.isfile(file_path):
        return jsonify({"status": "error", "message": "Document not found"}), 404
    return send_file(file_path)
