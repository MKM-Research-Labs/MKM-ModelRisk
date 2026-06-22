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

"""Data lineage routes: manifest, trace, and staleness check."""

import logging
from datetime import datetime

from flask import jsonify, request

from routes.governance import governance_bp
from routes.governance._helpers import _load_lineage

from ._trace import _check_staleness, _trace_data, _PIPELINE_STEPS  # noqa: F401

logger = logging.getLogger(__name__)


@governance_bp.route("/governance/data-lineage", methods=["GET"])
def get_data_lineage():
    """Return pipeline manifest with live staleness check."""
    lineage = _load_lineage()

    try:
        step_statuses = _check_staleness(lineage)
    except Exception as e:
        logger.error("Staleness check failed: %s", e)
        step_statuses = []

    fresh = sum(1 for s in step_statuses if s["status"] == "fresh")
    stale = sum(1 for s in step_statuses if s["status"] == "stale")
    missing = sum(1 for s in step_statuses if s["status"] == "missing")

    return jsonify({
        "status": "success",
        "pipeline_steps": step_statuses,
        "summary": {
            "total": len(step_statuses),
            "fresh": fresh,
            "stale": stale,
            "missing": missing,
            "health": "healthy" if missing == 0 and stale == 0
                      else "degraded" if missing == 0
                      else "unhealthy",
        },
        "manifest": lineage,
        "as_of": datetime.now().isoformat(),
    })


@governance_bp.route("/governance/data-lineage/trace", methods=["GET"])
def trace_data_lineage():
    """Trace a data_type/data_id through the pipeline."""
    data_type = request.args.get("data_type", "").strip()
    data_id = request.args.get("data_id", "").strip()

    if not data_type or not data_id:
        return jsonify({
            "status": "error",
            "message": "Both data_type and data_id query params are required",
        }), 400

    lineage = _load_lineage()

    try:
        trace = _trace_data(lineage, data_type, data_id)
    except Exception as e:
        logger.error("Trace failed for %s/%s: %s", data_type, data_id, e)
        return jsonify({
            "status": "error",
            "message": "Internal server error",
        }), 500

    return jsonify({
        "status": "success",
        "data_type": data_type,
        "data_id": data_id,
        "trace": trace,
        "found": len(trace) > 0,
    })


@governance_bp.route("/governance/data-lineage/staleness", methods=["GET"])
def check_staleness():
    """Pipeline health check — returns per-step staleness."""
    lineage = _load_lineage()

    try:
        step_statuses = _check_staleness(lineage)
    except Exception as e:
        logger.error("Staleness check failed: %s", e)
        return jsonify({"status": "error", "message": "Internal server error"}), 500

    fresh = sum(1 for s in step_statuses if s["status"] == "fresh")
    total = len(step_statuses)

    return jsonify({
        "status": "success",
        "steps": step_statuses,
        "health_pct": round(100 * fresh / max(total, 1), 1),
        "as_of": datetime.now().isoformat(),
    })
