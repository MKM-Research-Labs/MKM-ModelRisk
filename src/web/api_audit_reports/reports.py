# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Reading what has been generated: the catalogue, the files, the coverage report.

Every route here is a GET. Producing the artefacts is ``generate``; this only serves
what is on disk, so nothing in it can fail because a report failed to render.
"""
from __future__ import annotations

import os

from flask import abort, jsonify, send_from_directory

from config.audit import COVERAGE_HTML_DIRNAME
from src.web.api_audit_reports import _bp, _suite
from src.web.api_audit_reports._bp import audit_reports_bp, catalogue


@audit_reports_bp.get("")
def list_reports():
    return jsonify(catalogue())


@audit_reports_bp.get("/coverage")
def serve_coverage_index():
    """Serve the browsable HTML coverage report's index page."""
    cov_dir = _bp.OUTPUT_DIR / COVERAGE_HTML_DIRNAME
    if not (cov_dir / "index.html").is_file():
        abort(404)
    return send_from_directory(cov_dir, "index.html")


@audit_reports_bp.get("/coverage/<path:filename>")
def serve_coverage_asset(filename: str):
    """Serve a static asset (css/js/per-file page) of the coverage HTML report."""
    cov_dir = _bp.OUTPUT_DIR / COVERAGE_HTML_DIRNAME
    if not cov_dir.is_dir():
        abort(404)
    return send_from_directory(cov_dir, filename)


@audit_reports_bp.get("/<path:filename>")
def serve_report(filename: str):
    # send_from_directory rejects path traversal and missing files with 404.
    # PDFs render inline; XML/JSON/TXT download as attachments.
    if not _bp.OUTPUT_DIR.is_dir():
        abort(404)
    as_attachment = os.path.splitext(filename)[1].lower() != ".pdf"
    return send_from_directory(_bp.OUTPUT_DIR, filename, as_attachment=as_attachment)


@audit_reports_bp.get("/coverage-status")
def coverage_status():
    """Poll target for the UI while a background coverage refresh runs."""
    with _suite.cov_lock:
        return jsonify({"running": _suite.cov_state["running"],
                        "error": _suite.cov_state["error"]})
