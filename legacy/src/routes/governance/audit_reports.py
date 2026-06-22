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

"""Audit reports listing and download routes."""

import os
from datetime import datetime

from flask import abort, jsonify, send_from_directory

from . import governance_bp
from ._constants import AUDIT_REPORTS_DIR

_TYPE_LABELS = {
    '.pdf':  'PDF',
    '.xml':  'XML',
    '.html': 'HTML',
    '.tex':  'LaTeX',
    '.log':  'Log',
}

# Files never shown in the audit tab
_EXCLUDED = {'.DS_Store', 'test_failures_report.json', '_run_test_report.py'}


@governance_bp.route("/governance/audit-reports", methods=["GET"])
def list_audit_reports():
    """List all artefacts in the audit output directory."""
    if not os.path.isdir(AUDIT_REPORTS_DIR):
        return jsonify({"status": "success", "reports": [],
                        "coverage_available": False})

    reports = []
    coverage_available = os.path.isfile(
        os.path.join(AUDIT_REPORTS_DIR, "coverage", "index.html"))

    for fname in sorted(os.listdir(AUDIT_REPORTS_DIR)):
        if fname in _EXCLUDED or fname.startswith('.'):
            continue
        fpath = os.path.join(AUDIT_REPORTS_DIR, fname)
        if not os.path.isfile(fpath):
            continue
        ext = os.path.splitext(fname)[1].lower()
        stat = os.stat(fpath)
        reports.append({
            "filename": fname,
            "type": _TYPE_LABELS.get(ext, ext.lstrip('.').upper() or 'FILE'),
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        })

    return jsonify({
        "status": "success",
        "reports": reports,
        "coverage_available": coverage_available,
    })


@governance_bp.route("/governance/audit-reports/file/<path:filename>",
                     methods=["GET"])
def download_audit_report(filename):
    """Serve an audit report file (inline for PDF, attachment for others)."""
    safe_path = os.path.realpath(os.path.join(AUDIT_REPORTS_DIR, filename))
    if not safe_path.startswith(os.path.realpath(AUDIT_REPORTS_DIR) + os.sep):
        abort(403)
    if not os.path.isfile(safe_path):
        abort(404)
    ext = os.path.splitext(filename)[1].lower()
    as_attachment = ext != '.pdf'
    return send_from_directory(
        AUDIT_REPORTS_DIR, filename, as_attachment=as_attachment)


@governance_bp.route("/governance/audit-reports/coverage", methods=["GET"])
def serve_coverage_index():
    """Serve the coverage HTML report index page."""
    cov_dir = os.path.join(AUDIT_REPORTS_DIR, "coverage")
    if not os.path.isfile(os.path.join(cov_dir, "index.html")):
        abort(404)
    return send_from_directory(cov_dir, "index.html")
