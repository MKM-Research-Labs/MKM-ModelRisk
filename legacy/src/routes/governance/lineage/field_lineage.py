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

"""Field-level lineage routes."""

import logging

from flask import jsonify, request

from routes.governance import governance_bp
from routes.governance._helpers import _load_field_lineage

logger = logging.getLogger(__name__)


@governance_bp.route("/governance/field-lineage", methods=["GET"])
def get_field_lineage():
    """Return the full field-level lineage registry.

    Optional query param: ?report=<report_key> to filter to one report.
    """
    registry = _load_field_lineage()
    if not registry:
        return jsonify({
            "status": "error",
            "message": "Field lineage registry not found. Run the pipeline first.",
        }), 404

    report_filter = request.args.get("report", "").strip()

    if report_filter:
        reports = registry.get("reports", {})
        if report_filter not in reports:
            return jsonify({
                "status": "error",
                "message": f"Report '{report_filter}' not found in registry",
                "available_reports": list(reports.keys()),
            }), 404
        filtered = {report_filter: reports[report_filter]}
    else:
        filtered = registry.get("reports", {})

    # Build summary
    total_fields = 0
    report_summaries = []
    for rkey, rdata in filtered.items():
        field_count = 0
        for section in rdata.get("sections", {}).values():
            field_count += len(section.get("fields", {}))
        total_fields += field_count
        report_summaries.append({
            "report": rkey,
            "label": rdata.get("label", rkey),
            "generator": rdata.get("generator", ""),
            "section_count": len(rdata.get("sections", {})),
            "field_count": field_count,
        })

    return jsonify({
        "status": "success",
        "version": registry.get("version", "unknown"),
        "reports": filtered,
        "summary": report_summaries,
        "total_fields": total_fields,
        "total_reports": len(filtered),
    })


@governance_bp.route("/governance/field-lineage/lookup", methods=["GET"])
def field_lineage_lookup():
    """Look up lineage for a specific field.

    Query params: ?report=<key>&section=<key>&field=<key>
    Or: ?search=<text> for fuzzy search across all fields.
    """
    registry = _load_field_lineage()
    if not registry:
        return jsonify({"status": "error", "message": "Registry not found"}), 404

    search = request.args.get("search", "").strip().lower()
    report_key = request.args.get("report", "").strip()
    section_key = request.args.get("section", "").strip()
    field_key = request.args.get("field", "").strip()

    reports = registry.get("reports", {})

    # Exact lookup
    if report_key and section_key and field_key:
        report = reports.get(report_key, {})
        section = report.get("sections", {}).get(section_key, {})
        field = section.get("fields", {}).get(field_key)
        if not field:
            return jsonify({
                "status": "error",
                "message": f"Field not found: {report_key}.{section_key}.{field_key}",
            }), 404
        return jsonify({
            "status": "success",
            "report": report_key,
            "section": section_key,
            "field": field_key,
            "lineage": field,
        })

    # Search across all fields
    if search:
        results = []
        for rkey, rdata in reports.items():
            for skey, sdata in rdata.get("sections", {}).items():
                for fkey, fdata in sdata.get("fields", {}).items():
                    searchable = " ".join([
                        fkey, fdata.get("label", ""),
                        fdata.get("source_field", ""),
                        fdata.get("cdm_path", "") or "",
                        fdata.get("computation", ""),
                    ]).lower()
                    if search in searchable:
                        results.append({
                            "report": rkey,
                            "report_label": rdata.get("label", rkey),
                            "section": skey,
                            "field": fkey,
                            "lineage": fdata,
                        })
        return jsonify({
            "status": "success",
            "query": search,
            "results": results,
            "count": len(results),
        })

    return jsonify({
        "status": "error",
        "message": "Provide ?search=<text> or ?report=&section=&field= params",
    }), 400
