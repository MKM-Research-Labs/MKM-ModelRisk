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

"""Model inventory routes: list, detail, update fields."""

import logging
from collections import Counter
from datetime import datetime

from flask import jsonify, request

from . import governance_bp
from ._constants import EDITABLE_FIELDS
from ._helpers import (
    _find_model,
    _get_model_or_404,
    _load_inventory,
    _save_inventory,
    _load_audit_log,
    _save_audit_log,
    _vq_summary,
)

logger = logging.getLogger(__name__)


@governance_bp.route("/governance/models", methods=["GET"])
def get_models():
    """Get model inventory summary for dashboard."""
    inventory = _load_inventory()
    if not inventory:
        return jsonify({"status": "error", "message": "Model inventory not found"}), 404

    models = inventory.get("models", [])
    today = datetime.now().strftime("%Y-%m-%d")

    summary = []
    for m in models:
        # Calculate review status
        next_review = m.get("next_review_date")
        if next_review:
            days_to_review = (datetime.strptime(next_review, "%Y-%m-%d") - datetime.now()).days
            if days_to_review < 0:
                review_status = "Overdue"
            elif days_to_review <= 30:
                review_status = "Due Soon"
            elif days_to_review <= 90:
                review_status = "Upcoming"
            else:
                review_status = "On Track"
        else:
            review_status = "Not Scheduled"

        # remediation_steps may be either list-of-dicts (structured) or
        # list-of-strings (legacy/freeform). String entries can't have a
        # status, so they're counted as 0 open. Defensive against either
        # shape to avoid 500-ing the whole inventory endpoint.
        remediation_steps = m.get("remediation_steps") or []
        open_remediations = sum(
            1 for r in remediation_steps
            if isinstance(r, dict) and r.get("status") == "Open"
        )

        summary.append({
            "model_id": m["model_id"],
            "name": m["name"],
            "short_name": m["short_name"],
            "category": m["category"],
            "tier": m["tier"],
            "materiality": m["materiality"],
            "complexity": m["complexity"],
            "status": m["status"],
            "lifecycle_stage": m["lifecycle_stage"],
            "version": m["version"],
            "owner": m["owner"],
            "validation_status": m["validation_status"],
            "next_review_date": next_review,
            "last_review_date": m.get("last_review_date"),
            "rag_rating": m.get("rag_rating", "Not Rated"),
            "mrc_signoff_date": m.get("mrc_signoff_date"),
            "recertification_date": m.get("recertification_date"),
            "review_frequency": m.get("review_frequency"),
            "review_status": review_status,
            "upstream_count": len(m.get("upstream_models", [])),
            "downstream_count": len(m.get("downstream_models", [])),
            "limitations_count": len(m.get("limitations", [])),
            "assumptions_count": len(m.get("assumptions", [])),
            "open_remediations": open_remediations,
            # test_coverage may be a dict (structured) or a string (legacy
            # freeform). Only ask for keys when it's a dict.
            "has_benchmark": (
                m.get("test_coverage", {}).get("benchmark_tests", False)
                if isinstance(m.get("test_coverage"), dict) else False
            ),
            "risk_rating": (
                m.get("overall_risk_rating", {}).get("effective_rating", "Not Rated")
                if isinstance(m.get("overall_risk_rating"), dict) else "Not Rated"
            ),
            "validation_coverage": _vq_summary(m),
        })

    tier_counts = Counter(s["tier"] for s in summary)
    category_counts = Counter(s["category"] for s in summary)
    status_counts = Counter(s["review_status"] for s in summary)

    return jsonify({
        "status": "success",
        "models": summary,
        "total_models": len(summary),
        "tier_distribution": tier_counts,
        "category_distribution": category_counts,
        "review_status_distribution": status_counts,
        "model_chain": inventory.get("model_chain"),
        "tiering_matrix": inventory.get("tiering_matrix"),
        "metadata": inventory.get("metadata"),
        "as_of": today,
    })


@governance_bp.route("/governance/models/<model_id>/update", methods=["POST"])
def update_model_field(model_id):
    """Update a model field with audit trail.

    Expects JSON: {field, value, reason, user}
    """
    result = _get_model_or_404(model_id)
    if not isinstance(result[1], dict):
        return result  # error response
    inventory, model = result

    data = request.get_json(silent=True) or {}
    field = data.get("field")
    new_value = data.get("value")
    reason = data.get("reason", "").strip()
    user = data.get("user", "unknown")

    if not field or field not in EDITABLE_FIELDS:
        return jsonify({
            "status": "error",
            "message": f"Field '{field}' is not editable. Editable fields: {list(EDITABLE_FIELDS.keys())}",
        }), 400

    if not reason:
        return jsonify({"status": "error", "message": "A reason is required for all changes"}), 400

    if new_value is None or str(new_value).strip() == "":
        return jsonify({"status": "error", "message": "A value is required"}), 400

    field_spec = EDITABLE_FIELDS[field]
    if field_spec["type"] == "choice" and new_value not in field_spec["options"]:
        return jsonify({
            "status": "error",
            "message": f"Invalid value '{new_value}'. Options: {field_spec['options']}",
        }), 400

    old_value = model.get(field)
    model[field] = new_value

    if not _save_inventory(inventory):
        return jsonify({"status": "error", "message": "Failed to save inventory"}), 500

    # Log to audit trail
    audit_entry = {
        "timestamp": datetime.now().isoformat(),
        "model_id": model_id,
        "event_type": "field_update",
        "user": user,
        "action": f"Updated {field}",
        "parameters": {
            "field": field,
            "old_value": old_value,
            "new_value": new_value,
        },
        "context": reason,
        "source": "governance_ui",
    }

    audit_log = _load_audit_log()
    audit_log.append(audit_entry)
    if len(audit_log) > 10000:
        audit_log = audit_log[-10000:]
    _save_audit_log(audit_log)

    logger.info("Model %s: %s changed from '%s' to '%s' by %s. Reason: %s",
                model_id, field, old_value, new_value, user, reason)

    return jsonify({
        "status": "success",
        "model_id": model_id,
        "field": field,
        "old_value": old_value,
        "new_value": new_value,
        "audit_entry": audit_entry,
    })


@governance_bp.route("/governance/editable-fields", methods=["GET"])
def get_editable_fields():
    """Return the list of editable fields and their types/options."""
    return jsonify({"status": "success", "fields": EDITABLE_FIELDS})


@governance_bp.route("/governance/models/<model_id>", methods=["GET"])
def get_model_detail(model_id):
    """Get full detail for a single model."""
    result = _get_model_or_404(model_id)
    if not isinstance(result[1], dict):
        return result  # error response
    inventory, model = result

    # Load recent audit entries for this model
    audit_log = _load_audit_log()
    model_audit = [e for e in audit_log if e.get("model_id") == model_id][-50:]

    return jsonify({
        "status": "success",
        "model": model,
        "audit_entries": model_audit,
    })
