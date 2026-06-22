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

"""Validation question updates and risk-rating endpoints."""

import logging
from datetime import datetime

from flask import jsonify, request

from . import governance_bp
from ._constants import VALID_RISK_RATINGS, VALID_VQ_STATUSES
from ._helpers import (
    _calculate_risk_rating,
    _get_model_or_404,
    _load_audit_log,
    _save_audit_log,
    _save_inventory,
)

logger = logging.getLogger(__name__)


@governance_bp.route(
    "/governance/models/<model_id>/validation-questions/<int:question_id>/update",
    methods=["POST"],
)
def update_validation_question(model_id, question_id):
    """Update a single validation question's response for a model.

    Expects JSON: {status, evidence, reviewed_by}
    """
    result = _get_model_or_404(model_id)
    if not isinstance(result[1], dict):
        return result  # error response
    inventory, model = result

    questions = model.get("validation_questions", [])
    question = None
    for q in questions:
        if q["question_id"] == question_id:
            question = q
            break
    if not question:
        return jsonify({"status": "error", "message": f"Question {question_id} not found"}), 404

    data = request.get_json(silent=True) or {}
    new_status = data.get("status")
    evidence = data.get("evidence", "")
    reviewed_by = data.get("reviewed_by", "unknown")

    if not new_status or new_status not in VALID_VQ_STATUSES:
        return jsonify({
            "status": "error",
            "message": f"Invalid status. Must be one of: {VALID_VQ_STATUSES}",
        }), 400

    old_status = question.get("status")
    question["status"] = new_status
    question["evidence"] = evidence
    question["reviewed_by"] = reviewed_by
    question["last_reviewed"] = datetime.now().strftime("%Y-%m-%d")

    # Recalculate risk rating
    calc = _calculate_risk_rating(model)
    rr = model.setdefault("overall_risk_rating", {})
    rr["calculated_rating"] = calc["calculated_rating"]
    rr["calculated_score"] = calc["calculated_score"]
    rr["component_scores"] = calc["component_scores"]
    rr["last_calculated"] = datetime.now().isoformat()
    rr["effective_rating"] = rr.get("mrc_override") or calc["calculated_rating"]

    if not _save_inventory(inventory):
        return jsonify({"status": "error", "message": "Failed to save inventory"}), 500

    # Audit trail
    audit_entry = {
        "timestamp": datetime.now().isoformat(),
        "model_id": model_id,
        "event_type": "validation_question_update",
        "user": reviewed_by,
        "action": f"Updated validation Q{question_id}: {question['short_label']}",
        "parameters": {
            "question_id": question_id,
            "old_status": old_status,
            "new_status": new_status,
        },
        "context": evidence[:200] if evidence else "",
        "source": "governance_ui",
    }
    audit_log = _load_audit_log()
    audit_log.append(audit_entry)
    if len(audit_log) > 10000:
        audit_log = audit_log[-10000:]
    _save_audit_log(audit_log)

    logger.info("Model %s: validation Q%d status changed %s -> %s by %s",
                model_id, question_id, old_status, new_status, reviewed_by)

    return jsonify({"status": "success", "model": model, "audit_entry": audit_entry})


@governance_bp.route("/governance/models/<model_id>/risk-rating", methods=["GET"])
def get_risk_rating(model_id):
    """Calculate and return the composite risk rating for a model."""
    result = _get_model_or_404(model_id)
    if not isinstance(result[1], dict):
        return result  # error response
    inventory, model = result

    calc = _calculate_risk_rating(model)

    # Persist calculated result
    rr = model.setdefault("overall_risk_rating", {})
    rr["calculated_rating"] = calc["calculated_rating"]
    rr["calculated_score"] = calc["calculated_score"]
    rr["component_scores"] = calc["component_scores"]
    rr["last_calculated"] = datetime.now().isoformat()
    rr["effective_rating"] = rr.get("mrc_override") or calc["calculated_rating"]

    _save_inventory(inventory)

    return jsonify({
        "status": "success",
        "model_id": model_id,
        "risk_rating": rr,
    })


@governance_bp.route("/governance/models/<model_id>/risk-rating/override", methods=["POST"])
def override_risk_rating(model_id):
    """Apply or clear MRC override of risk rating.

    Expects JSON: {rating, reason, user}
    Set rating to null to clear override.
    """
    result = _get_model_or_404(model_id)
    if not isinstance(result[1], dict):
        return result  # error response
    inventory, model = result

    data = request.get_json(silent=True) or {}
    new_rating = data.get("rating")
    reason = data.get("reason", "").strip()
    user = data.get("user", "unknown")

    if new_rating is not None and new_rating not in VALID_RISK_RATINGS:
        return jsonify({
            "status": "error",
            "message": f"Invalid rating. Must be one of: {VALID_RISK_RATINGS} or null to clear",
        }), 400

    if not reason:
        return jsonify({"status": "error", "message": "A reason is required"}), 400

    rr = model.setdefault("overall_risk_rating", {})
    old_override = rr.get("mrc_override")

    rr["mrc_override"] = new_rating
    rr["mrc_override_reason"] = reason if new_rating else None
    rr["mrc_override_date"] = datetime.now().strftime("%Y-%m-%d") if new_rating else None
    rr["mrc_override_by"] = user if new_rating else None
    rr["effective_rating"] = new_rating or rr.get("calculated_rating", "Not Rated")

    if not _save_inventory(inventory):
        return jsonify({"status": "error", "message": "Failed to save inventory"}), 500

    action = "Cleared MRC override" if new_rating is None else f"MRC override set to {new_rating}"
    audit_entry = {
        "timestamp": datetime.now().isoformat(),
        "model_id": model_id,
        "event_type": "risk_rating_override",
        "user": user,
        "action": action,
        "parameters": {
            "old_override": old_override,
            "new_override": new_rating,
        },
        "context": reason,
        "source": "governance_ui",
    }
    audit_log = _load_audit_log()
    audit_log.append(audit_entry)
    if len(audit_log) > 10000:
        audit_log = audit_log[-10000:]
    _save_audit_log(audit_log)

    logger.info("Model %s: risk rating override %s -> %s by %s. Reason: %s",
                model_id, old_override, new_rating, user, reason)

    return jsonify({"status": "success", "model": model, "audit_entry": audit_entry})
