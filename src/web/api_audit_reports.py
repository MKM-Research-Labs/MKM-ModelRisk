# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""HTTP API for generated audit report files (list, view/download, generate)."""
from __future__ import annotations

import shutil
import subprocess
from datetime import date, datetime

from flask import Blueprint, abort, jsonify, send_from_directory

from audit.__main__ import build_report, write_audit_reports
from audit.pdf import REPORT_LABELS
from config.audit import AUDIT_OUTPUT_DIR, AUDIT_REPORT_LABELS, USER_GUIDE_MD
from src.governance.model_inventory import list_models
from src.governance.model_inventory.report import render_report_pdf
from src.governance.mrc.pack import TectonicNotFound
from src.governance.mrc_settings import get_settings

# Module-level so tests can point it at a temporary directory.
OUTPUT_DIR = AUDIT_OUTPUT_DIR

audit_reports_bp = Blueprint("audit_reports", __name__, url_prefix="/api/audit-reports")


# Filename -> human label: the fixed reports plus every generated per-rule PDF.
_LABELS = {**AUDIT_REPORT_LABELS, **REPORT_LABELS}


def _catalogue() -> list[dict]:
    if not OUTPUT_DIR.is_dir():
        return []
    reports = []
    for path in sorted(OUTPUT_DIR.glob("*.pdf")):
        stat = path.stat()
        reports.append({
            "filename": path.name,
            "label": _LABELS.get(path.name, path.stem.replace("_", " ").title()),
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
        })
    return reports


@audit_reports_bp.get("")
def list_reports():
    return jsonify(_catalogue())


@audit_reports_bp.get("/<path:filename>")
def serve_report(filename: str):
    # send_from_directory rejects path traversal and missing files with 404.
    if not OUTPUT_DIR.is_dir():
        abort(404)
    return send_from_directory(OUTPUT_DIR, filename, mimetype="application/pdf")


def _render_user_guide(dest):
    """Publish the user guide as a PDF (skipped if pandoc is not installed)."""
    if shutil.which("pandoc") is None:
        return
    subprocess.run(
        ["pandoc", str(USER_GUIDE_MD), "-o", str(dest), "--pdf-engine=tectonic"],
        check=True, capture_output=True)


@audit_reports_bp.post("/generate")
def generate():
    """(Re)generate the audit report PDFs into the output directory."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    as_of = date.today().isoformat()
    try:
        # One standalone PDF per audit function (R1–R8) plus the consolidated
        # overview — the same set the ``python -m audit --pdf`` CLI emits.
        write_audit_reports(build_report(), as_of, OUTPUT_DIR)
        (OUTPUT_DIR / "model_risk_report.pdf").write_bytes(
            render_report_pdf(list_models(), get_settings(), as_of))
    except TectonicNotFound as exc:
        # Optional system dependency missing: surface an actionable 503 rather
        # than a raw 500 stack trace.
        return jsonify({"error": str(exc)}), 503
    _render_user_guide(OUTPUT_DIR / "user_guide.pdf")
    return jsonify(_catalogue())
