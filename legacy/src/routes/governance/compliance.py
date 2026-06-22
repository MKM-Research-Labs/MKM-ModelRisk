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

"""BCBS 239 self-assessment and RACI matrix routes."""

import os
import uuid
from datetime import datetime

from flask import jsonify, request, send_file

from . import governance_bp
from ._constants import (
    VALID_RACI_ROLE_IDS,
    _BCBS239_SCORE_STATUS,
    _docs_dir,
)
from ._helpers import (
    _load_bcbs239,
    _save_bcbs239,
    _load_raci,
    _save_raci,
    _load_audit_log,
    _save_audit_log,
)


# ── BCBS 239 ──

@governance_bp.route("/governance/bcbs239", methods=["GET"])
def get_bcbs239():
    """Get BCBS 239 self-assessment data."""
    data = _load_bcbs239()
    if not data:
        return jsonify({"status": "error", "message": "BCBS 239 assessment not found"}), 404
    return jsonify({"status": "success", "assessment": data})


@governance_bp.route("/governance/bcbs239/principles/<int:principle_id>/update", methods=["POST"])
def update_bcbs239_principle(principle_id):
    """Update a BCBS 239 principle assessment."""
    data = _load_bcbs239()
    if not data:
        return jsonify({"status": "error", "message": "BCBS 239 assessment not found"}), 404

    principle = next((p for p in data["principles"] if p["id"] == principle_id), None)
    if not principle:
        return jsonify({"status": "error", "message": f"Principle {principle_id} not found"}), 404

    updates = request.get_json(silent=True) or {}
    for field in ["score", "evidence", "gaps", "remediation", "target_date"]:
        if field in updates:
            principle[field] = updates[field]

    # Auto-derive status from score
    if "score" in updates:
        score = int(updates["score"])
        principle["score"] = score
        principle["status"] = _BCBS239_SCORE_STATUS.get(score, "Unknown")

    data["assessment_date"] = datetime.now().strftime("%Y-%m-%d")

    if not _save_bcbs239(data):
        return jsonify({"status": "error", "message": "Failed to save assessment"}), 500

    return jsonify({"status": "success", "assessment": data})


@governance_bp.route("/governance/bcbs239/pdf", methods=["GET"])
def get_bcbs239_pdf():
    """Serve the BCBS 239 self-assessment PDF."""
    pdf_path = os.path.join(_docs_dir, "bcbs239", "bcbs239_self_assessment.pdf")
    if not os.path.isfile(pdf_path):
        return jsonify({
            "status": "error",
            "message": "BCBS 239 PDF not yet generated. Run: python -m docs.models.bcbs239.assessment --pdf",
        }), 404
    return send_file(pdf_path, mimetype="application/pdf")


# ── RACI Matrix ──

@governance_bp.route("/governance/raci", methods=["GET"])
def get_raci_matrix():
    """Return full RACI matrix with roles, activities, and escalation triggers."""
    data = _load_raci()
    if data is None:
        return jsonify({"status": "error", "message": "RACI matrix not found"}), 404
    return jsonify({"status": "success", "raci": data})


@governance_bp.route(
    "/governance/raci/roles/<role_id>/update", methods=["POST"]
)
def update_raci_role(role_id):
    """Update a RACI role assignment."""
    data = _load_raci()
    if data is None:
        return jsonify({"status": "error", "message": "RACI matrix not found"}), 404

    role = next((r for r in data.get("roles", []) if r["role_id"] == role_id), None)
    if role is None:
        return jsonify({"status": "error", "message": f"Role {role_id} not found"}), 404

    body = request.get_json(force=True)
    if "assigned_to" in body:
        role["assigned_to"] = body["assigned_to"]
    if "backup" in body:
        role["backup"] = body["backup"]

    data["metadata"]["last_updated"] = datetime.now().strftime("%Y-%m-%d")

    if not _save_raci(data):
        return jsonify({"status": "error", "message": "Failed to save RACI matrix"}), 500

    # Audit log
    audit_entry = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        "event_type": "raci_role_update",
        "user": body.get("user", "Unknown"),
        "details": {
            "role_id": role_id,
            "assigned_to": role["assigned_to"],
            "backup": role["backup"],
        },
    }
    entries = _load_audit_log()
    entries.append(audit_entry)
    _save_audit_log(entries)

    return jsonify({"status": "success", "raci": data, "audit_entry": audit_entry})


@governance_bp.route(
    "/governance/raci/activities/<activity_id>/update", methods=["POST"]
)
def update_raci_activity(activity_id):
    """Update RACI assignments for an activity."""
    data = _load_raci()
    if data is None:
        return jsonify({"status": "error", "message": "RACI matrix not found"}), 404

    activity = next(
        (a for a in data.get("activities", []) if a["activity_id"] == activity_id),
        None,
    )
    if activity is None:
        return jsonify(
            {"status": "error", "message": f"Activity {activity_id} not found"}
        ), 404

    body = request.get_json(force=True)

    # Validate role IDs
    for code in ["R", "A", "C", "I"]:
        if code in body:
            val = body[code]
            if val is not None and val not in VALID_RACI_ROLE_IDS:
                return jsonify(
                    {"status": "error", "message": f"Invalid role ID: {val}"}
                ), 400
            activity[code] = val

    if "notes" in body:
        activity["notes"] = body["notes"]
    if "tier_emphasis" in body:
        activity["tier_emphasis"] = body["tier_emphasis"]

    data["metadata"]["last_updated"] = datetime.now().strftime("%Y-%m-%d")

    if not _save_raci(data):
        return jsonify({"status": "error", "message": "Failed to save RACI matrix"}), 500

    audit_entry = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        "event_type": "raci_activity_update",
        "user": body.get("user", "Unknown"),
        "details": {
            "activity_id": activity_id,
            "R": activity["R"],
            "A": activity["A"],
            "C": activity["C"],
            "I": activity["I"],
        },
    }
    entries = _load_audit_log()
    entries.append(audit_entry)
    _save_audit_log(entries)

    return jsonify({"status": "success", "raci": data, "audit_entry": audit_entry})


@governance_bp.route(
    "/governance/raci/escalation-triggers/<trigger_id>/update", methods=["POST"]
)
def update_raci_escalation(trigger_id):
    """Update an escalation trigger's thresholds."""
    data = _load_raci()
    if data is None:
        return jsonify({"status": "error", "message": "RACI matrix not found"}), 404

    trigger = next(
        (t for t in data.get("escalation_triggers", []) if t["trigger_id"] == trigger_id),
        None,
    )
    if trigger is None:
        return jsonify(
            {"status": "error", "message": f"Trigger {trigger_id} not found"}
        ), 404

    body = request.get_json(force=True)
    if "tier_threshold" in body:
        trigger["tier_threshold"] = body["tier_threshold"]
    if "response_required" in body:
        trigger["response_required"] = body["response_required"]

    data["metadata"]["last_updated"] = datetime.now().strftime("%Y-%m-%d")

    if not _save_raci(data):
        return jsonify({"status": "error", "message": "Failed to save RACI matrix"}), 500

    audit_entry = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        "event_type": "raci_escalation_update",
        "user": body.get("user", "Unknown"),
        "details": {
            "trigger_id": trigger_id,
            "tier_threshold": trigger["tier_threshold"],
            "response_required": trigger["response_required"],
        },
    }
    entries = _load_audit_log()
    entries.append(audit_entry)
    _save_audit_log(entries)

    return jsonify({"status": "success", "raci": data, "audit_entry": audit_entry})
