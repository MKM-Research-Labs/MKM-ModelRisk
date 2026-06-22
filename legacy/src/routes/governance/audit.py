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

"""Audit-trail logging and PDF document serving routes.

Validation-question and risk-rating endpoints live in
``audit_validation.py``; this file is also the registrar for that module.
"""

import logging
import os
from datetime import datetime

from flask import jsonify, request, send_file

from . import governance_bp
from ._constants import _MODEL_DOC_DIRS, _docs_dir
from ._helpers import (
    _get_model_or_404,
    _load_audit_log,
    _save_audit_log,
)

# Register validation-question / risk-rating routes (imported for side
# effects — registers handlers on ``governance_bp``).
from . import audit_validation  # noqa: E402, F401

logger = logging.getLogger(__name__)


# ── Audit log ──

@governance_bp.route("/governance/models/<model_id>/audit", methods=["POST"])
def log_model_usage(model_id):
    """Log a model usage event to the audit trail."""
    result = _get_model_or_404(model_id)
    if not isinstance(result[1], dict):
        return result  # error response

    data = request.get_json(silent=True) or {}

    entry = {
        "timestamp": datetime.now().isoformat(),
        "model_id": model_id,
        "event_type": data.get("event_type", "usage"),
        "user": data.get("user", "system"),
        "action": data.get("action", ""),
        "parameters": data.get("parameters", {}),
        "context": data.get("context", ""),
        "source": data.get("source", "api"),
    }

    audit_log = _load_audit_log()
    audit_log.append(entry)

    # Keep last 10000 entries
    if len(audit_log) > 10000:
        audit_log = audit_log[-10000:]

    if not _save_audit_log(audit_log):
        return jsonify({"status": "error", "message": "Failed to save audit entry"}), 500

    return jsonify({"status": "success", "entry": entry})


@governance_bp.route("/governance/audit-trail", methods=["GET"])
def get_audit_trail():
    """Get audit trail with optional filtering."""
    model_id = request.args.get("model_id")
    event_type = request.args.get("event_type")
    limit = request.args.get("limit", 100, type=int)

    audit_log = _load_audit_log()

    if model_id:
        audit_log = [e for e in audit_log if e.get("model_id") == model_id]

    if event_type:
        audit_log = [e for e in audit_log if e.get("event_type") == event_type]

    # Return most recent entries
    entries = audit_log[-limit:]
    entries.reverse()

    return jsonify({
        "status": "success",
        "entries": entries,
        "total_entries": len(audit_log),
        "returned": len(entries),
    })


# ── PDF document serving ──

@governance_bp.route("/governance/models/<model_id>/documentation/pdf", methods=["GET"])
def get_model_documentation_pdf(model_id):
    """Serve per-model documentation PDF."""
    doc_dir = _MODEL_DOC_DIRS.get(model_id)
    if not doc_dir:
        return jsonify({"status": "error", "message": f"No documentation directory for {model_id}"}), 404

    # Model doc PDF matches directory name (e.g. gev_hazard/gev_hazard.pdf)
    pdf_name = doc_dir + ".pdf"
    pdf_path = os.path.join(_docs_dir, doc_dir, pdf_name)
    if not os.path.isfile(pdf_path):
        return jsonify({"status": "error", "message": f"Documentation PDF not found for {model_id}"}), 404

    return send_file(pdf_path, mimetype="application/pdf")


@governance_bp.route("/governance/models/<model_id>/test-results/pdf", methods=["GET"])
def get_model_test_results_pdf(model_id):
    """Serve per-model test results PDF."""
    doc_dir = _MODEL_DOC_DIRS.get(model_id)
    if not doc_dir:
        return jsonify({"status": "error", "message": f"No documentation directory for {model_id}"}), 404

    pdf_path = os.path.join(_docs_dir, doc_dir, "test_results.pdf")
    if not os.path.isfile(pdf_path):
        return jsonify({"status": "error", "message": "Test results PDF not yet generated. Run: python app.py check tests --pdf"}), 404

    return send_file(pdf_path, mimetype="application/pdf")


@governance_bp.route("/governance/models/<model_id>/analysis/pdf", methods=["GET"])
def get_model_analysis_pdf(model_id):
    """Serve per-model analysis PDF (sensitivity analysis, stress testing)."""
    doc_dir = _MODEL_DOC_DIRS.get(model_id)
    if not doc_dir:
        return jsonify({"status": "error", "message": f"No documentation directory for {model_id}"}), 404

    pdf_path = os.path.join(_docs_dir, doc_dir, "analysis.pdf")
    if not os.path.isfile(pdf_path):
        return jsonify({"status": "error", "message": "Analysis PDF not yet generated. Run: python -m docs.models.sensitivities.generate_all_analysis"}), 404

    return send_file(pdf_path, mimetype="application/pdf")


# ── User guide PDF serving (per-workflow) ──

_USER_GUIDE_PDFS = {
    "storm-control":        ("storm_control",        "storm_control_guide.pdf"),
    "gauge-prs-pricing":    ("gauge_prs_pricing",    "gauge_prs_pricing_guide.pdf"),
    "property-prs-pricing": ("property_prs_pricing", "property_prs_pricing_guide.pdf"),
    "market-making":        ("market_making",        "market_making_guide.pdf"),
    "eod-process":          ("eod_process",          "eod_process_guide.pdf"),
    "stress-testing":       ("stress_testing",       "stress_testing_guide.pdf"),
}


@governance_bp.route("/governance/<guide_key>/guide/pdf", methods=["GET"])
def get_user_guide_pdf(guide_key):
    """Serve a workflow user guide PDF."""
    entry = _USER_GUIDE_PDFS.get(guide_key)
    if entry is None:
        return jsonify({"status": "error", "message": f"Unknown guide: {guide_key}"}), 404

    doc_dir, pdf_name = entry
    pdf_path = os.path.join(_docs_dir, doc_dir, pdf_name)
    if not os.path.isfile(pdf_path):
        return jsonify({
            "status": "error",
            "message": f"Guide PDF not yet generated. "
                       f"Run: make -C docs/models/{doc_dir}/",
        }), 404

    return send_file(pdf_path, mimetype="application/pdf")


@governance_bp.route("/governance/mrc/terms-of-reference/pdf", methods=["GET"])
def get_mrc_tor_pdf():
    """Serve the MRC Terms of Reference PDF."""
    pdf_path = os.path.join(_docs_dir, "mrc_tor", "mrc_terms_of_reference.pdf")
    if not os.path.isfile(pdf_path):
        return jsonify({"status": "error", "message": "MRC ToR PDF not yet generated. Run: python -m docs.models.mrc_tor.generator --pdf"}), 404

    return send_file(pdf_path, mimetype="application/pdf")
