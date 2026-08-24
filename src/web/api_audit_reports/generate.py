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
"""(Re)generating the audit-evidence package: the one POST in this API.

One click renders every rule report, the consolidated overview, the Model Risk
Report, the completeness audit and the guides, then hands the ~1-minute test suite
to a background thread. A single report failing is recorded and reported rather
than aborting the run, so one bad render cannot leave every later report stale.
"""
from __future__ import annotations

from datetime import date

from flask import jsonify

from audit.__main__ import build_report, write_audit_reports, write_init_audit_json
from config.audit import COMPLETENESS_REPORT_PDF_NAME, INTEGRATION_GUIDE_PDF_NAME
from src.governance.completeness.report import render_completeness_pdf
from src.governance.model_inventory import list_models
from src.governance.model_inventory.report import render_report_pdf
from src.governance.mrc.pack import TectonicNotFound
from src.governance.mrc_settings import get_settings
from src.web.api_audit_reports import _bp, _suite
from src.web.api_audit_reports._bp import audit_reports_bp, catalogue
from src.web.api_audit_reports._guides import (render_integration_guide,
                                               render_user_guide,
                                               render_user_guide_docx)


def write_one(dest, render, errors: list) -> None:
    """Render one report to ``dest``, recording a non-fatal failure in ``errors``.

    ``TectonicNotFound`` still propagates (no engine → nothing can be produced);
    any other failure is recorded by filename and the caller moves on to the next
    report, so one bad report never leaves the rest stale.
    """
    try:
        dest.write_bytes(render())
    except TectonicNotFound:
        raise
    except Exception as exc:                     # noqa: BLE001 — recorded, not swallowed
        errors.append((dest.name, str(exc)))


@audit_reports_bp.post("/generate")
def generate():
    """(Re)generate the audit report PDFs into the output directory.

    A single report failing (e.g. a one-off tectonic compile error) no longer
    aborts the run: the remaining reports are still refreshed and the failed ones
    are returned under ``failures`` so the UI can name what is now stale, rather
    than every report after the failure silently keeping its previous date.
    """
    _bp.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    as_of = date.today().isoformat()
    report = build_report()
    errors: list = []
    try:
        with _suite.write_lock:                  # serialise vs. the bg rebuild
            # One standalone PDF per audit function (R1–R8) plus the JSON-file
            # audit and the consolidated overview — the same set the ``python -m
            # audit --pdf`` CLI emits — followed by the Model Risk report.
            write_audit_reports(report, as_of, _bp.OUTPUT_DIR, errors=errors)
            settings = get_settings()
            write_one(_bp.OUTPUT_DIR / "model_risk_report.pdf",
                      lambda: render_report_pdf(list_models(), settings, as_of), errors)
            # The completeness audit reads the registers and the document store
            # itself, so it takes no model list: what it reports is partly what
            # the store does *not* hold, which a list of records cannot express.
            write_one(_bp.OUTPUT_DIR / COMPLETENESS_REPORT_PDF_NAME,
                      lambda: render_completeness_pdf(settings, as_of), errors)
    except TectonicNotFound as exc:
        # Optional system dependency missing: surface an actionable 503 rather
        # than a raw 500 stack trace.
        return jsonify({"error": str(exc)}), 503
    # Machine-readable __init__ audit export sits next to the PDFs.
    write_init_audit_json(report, _bp.OUTPUT_DIR)
    render_user_guide(_bp.OUTPUT_DIR / "user_guide.pdf")
    render_user_guide_docx(_bp.OUTPUT_DIR / "user_guide.docx")
    render_integration_guide(_bp.OUTPUT_DIR / INTEGRATION_GUIDE_PDF_NAME)
    # Run the suites in the background; coverage/JUnit/Test Report land when done.
    _suite.start_coverage_refresh(_bp.OUTPUT_DIR)
    return jsonify({
        "reports": catalogue(),
        "failures": [{"file": name, "error": msg} for name, msg in errors],
    })
