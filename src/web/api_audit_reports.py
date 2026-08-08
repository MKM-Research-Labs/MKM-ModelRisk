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
"""HTTP API for generated audit report files (list, view/download, generate).

The Generate action produces the full audit-evidence package into a single
directory — the per-rule and consolidated PDFs plus the ``__init__`` JSON export
immediately, and then (in the background, since the suite takes ~1 min) the
coverage/JUnit artefacts and the Test Report, mirroring PhysicalRisk where the
audit run itself drops coverage, JUnit and the browsable coverage HTML alongside
the reports. The tab lists every artefact, not only the PDFs.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import threading
from datetime import date, datetime

from flask import Blueprint, abort, jsonify, send_from_directory

from audit.__main__ import build_report, write_audit_reports, write_init_audit_json
from audit.coverage import coverage_summary
from audit.pdf import REPORT_LABELS, render_test_report_pdf
from audit.testsuite import SUITE_ACTIVE_ENV, run_test_suite
from config.audit import (AUDIT_OUTPUT_DIR, AUDIT_REPORT_LABELS,
                          COMPLETENESS_REPORT_PDF_NAME, COVERAGE_HTML_DIRNAME,
                          COVERAGE_HTML_LABEL, COVERAGE_XML_NAME,
                          TEST_REPORT_PDF_NAME, USER_GUIDE_MD)
from src.governance.latex import front_matter, history_page, logo_asset, preamble
from src.governance.model_inventory import list_models
from src.governance.completeness.report import render_completeness_pdf
from src.governance.model_inventory.report import render_report_pdf
from src.governance.mrc.pack import TectonicNotFound, compile_tex
from src.governance.mrc_settings import get_settings

# Module-level so tests can point it at a temporary directory.
OUTPUT_DIR = AUDIT_OUTPUT_DIR

audit_reports_bp = Blueprint("audit_reports", __name__, url_prefix="/api/audit-reports")


# Filename -> human label: the fixed reports plus every generated per-rule PDF.
_LABELS = {**AUDIT_REPORT_LABELS, **REPORT_LABELS}

# File extension -> short type badge shown in the tab.
_TYPE_LABELS = {".pdf": "PDF", ".xml": "XML", ".json": "JSON",
                ".txt": "TXT", ".html": "HTML"}

# Background full-suite refresh. The suite takes ~1 min, so generation returns
# immediately and refreshes the coverage/JUnit artefacts, the Test Report and the
# coverage-dependent reports (R3 + the consolidated overview) once it lands.
_cov_lock = threading.Lock()
_cov_state = {"running": False, "error": None}


def _run_coverage_and_rebuild(output_dir) -> None:
    """Run the suites into ``output_dir``, then rebuild the coverage-aware output.

    Emits ``coverage.xml``/``coverage/`` HTML/``junit.xml`` (+ best-effort
    ``e2e_junit.xml``), writes the Test Report from the parsed results, and
    re-renders the reports so R3 and the consolidated overview show live numbers.
    """
    global _cov_state
    try:
        results = run_test_suite(output_dir)
        as_of = date.today().isoformat()
        cov = coverage_summary(output_dir / COVERAGE_XML_NAME)
        (output_dir / TEST_REPORT_PDF_NAME).write_bytes(
            render_test_report_pdf(results, cov, as_of))
        write_audit_reports(build_report(), as_of, output_dir)
        error = None
    except Exception as exc:                    # missing pytest, timeout, tectonic…
        error = str(exc)
    with _cov_lock:
        _cov_state["running"] = False
        _cov_state["error"] = error


def _start_coverage_refresh(output_dir) -> bool:
    """Kick off a background suite/coverage refresh unless one is already running.

    Refuses to start when already inside a suite run (``SUITE_ACTIVE_ENV`` set) —
    e.g. an e2e test that POSTs to /generate while the e2e suite itself runs under
    an audit run — so a suite never recursively spawns another suite.
    """
    if os.environ.get(SUITE_ACTIVE_ENV):
        return False
    with _cov_lock:
        if _cov_state["running"]:
            return False
        _cov_state["running"] = True
        _cov_state["error"] = None
    threading.Thread(target=_run_coverage_and_rebuild, args=(output_dir,),
                     daemon=True).start()
    return True


def _entry(path) -> dict:
    """Catalogue row for one artefact file ``path``."""
    stat = path.stat()
    ext = path.suffix.lower()
    return {
        "filename": path.name,
        "label": _LABELS.get(path.name, path.stem.replace("_", " ").title()),
        "type": _TYPE_LABELS.get(ext, ext.lstrip(".").upper() or "FILE"),
        "size": stat.st_size,
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
    }


def _catalogue() -> list[dict]:
    """Every artefact in the output dir, plus the browsable coverage HTML report."""
    if not OUTPUT_DIR.is_dir():
        return []
    reports = [_entry(path)
               for path in sorted(OUTPUT_DIR.iterdir())
               if path.is_file() and not path.name.startswith(".")]
    cov_index = OUTPUT_DIR / COVERAGE_HTML_DIRNAME / "index.html"
    if cov_index.is_file():
        stat = cov_index.stat()
        reports.append({
            "filename": f"{COVERAGE_HTML_DIRNAME}/index.html",
            "label": COVERAGE_HTML_LABEL,
            "type": "HTML",
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
            "href": "coverage",         # served by the coverage route, not the file route
        })
    return reports


@audit_reports_bp.get("")
def list_reports():
    return jsonify(_catalogue())


@audit_reports_bp.get("/coverage")
def serve_coverage_index():
    """Serve the browsable HTML coverage report's index page."""
    cov_dir = OUTPUT_DIR / COVERAGE_HTML_DIRNAME
    if not (cov_dir / "index.html").is_file():
        abort(404)
    return send_from_directory(cov_dir, "index.html")


@audit_reports_bp.get("/coverage/<path:filename>")
def serve_coverage_asset(filename: str):
    """Serve a static asset (css/js/per-file page) of the coverage HTML report."""
    cov_dir = OUTPUT_DIR / COVERAGE_HTML_DIRNAME
    if not cov_dir.is_dir():
        abort(404)
    return send_from_directory(cov_dir, filename)


@audit_reports_bp.get("/<path:filename>")
def serve_report(filename: str):
    # send_from_directory rejects path traversal and missing files with 404.
    # PDFs render inline; XML/JSON/TXT download as attachments.
    if not OUTPUT_DIR.is_dir():
        abort(404)
    as_attachment = os.path.splitext(filename)[1].lower() != ".pdf"
    return send_from_directory(OUTPUT_DIR, filename, as_attachment=as_attachment)


def _render_user_guide_docx(dest):
    """The same guide as an editable Word document. An adopter's own people mark a guide
    up and hand it back; a PDF cannot be worked on, so both forms are published from the
    one markdown source rather than diverging as two hand-kept documents."""
    if shutil.which("pandoc") is None:
        return
    subprocess.run(["pandoc", str(USER_GUIDE_MD), "-o", str(dest)],
                   check=True, capture_output=True, text=True)


def _render_user_guide(dest):
    """Publish the user guide as a PDF in the shared house style (skipped if pandoc
    or tectonic is absent). The markdown body is converted to a LaTeX fragment and
    wrapped in the standard preamble/title, so the guide matches every other PDF."""
    if shutil.which("pandoc") is None:
        return
    body = subprocess.run(
        ["pandoc", str(USER_GUIDE_MD), "-t", "latex"],
        check=True, capture_output=True, text=True).stdout
    as_of = date.today().isoformat()
    # The institution heads this document like every other one it publishes; the
    # guide is the only report that used to head itself with the platform's name.
    settings = get_settings()
    org = (settings.get("fields") or {}).get("org_name", "")
    assets = logo_asset(settings)
    tex = (
        preamble("User Guide", org_name=org)
        # pandoc's LaTeX uses \tightlist, which its standalone template defines;
        # a fragment does not, so provide it here.
        + "\\providecommand{\\tightlist}{\\setlength{\\itemsep}{0pt}\\setlength{\\parskip}{0pt}}\n"
        + "\\begin{document}\n"
        + front_matter("User Guide", "Model risk governance console", org_name=org,
                       date=as_of, logo=bool(assets), toc=True)
        + history_page(as_of, "User guide generated", org_name=org)
        + body
        + "\\end{document}\n"
    )
    try:
        dest.write_bytes(compile_tex(tex, assets))
    except TectonicNotFound:
        return


@audit_reports_bp.post("/generate")
def generate():
    """(Re)generate the audit report PDFs into the output directory."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    as_of = date.today().isoformat()
    report = build_report()
    try:
        # One standalone PDF per audit function (R1–R8) plus the JSON-file audit
        # and the consolidated overview — the same set the ``python -m audit
        # --pdf`` CLI emits — followed by the Model Risk report.
        write_audit_reports(report, as_of, OUTPUT_DIR)
        settings = get_settings()
        (OUTPUT_DIR / "model_risk_report.pdf").write_bytes(
            render_report_pdf(list_models(), settings, as_of))
        # The completeness audit reads the registers and the document store
        # itself, so it takes no model list: what it reports is partly what the
        # store does *not* hold, which a list of records cannot express.
        (OUTPUT_DIR / COMPLETENESS_REPORT_PDF_NAME).write_bytes(
            render_completeness_pdf(settings, as_of))
    except TectonicNotFound as exc:
        # Optional system dependency missing: surface an actionable 503 rather
        # than a raw 500 stack trace.
        return jsonify({"error": str(exc)}), 503
    # Machine-readable __init__ audit export sits next to the PDFs.
    write_init_audit_json(report, OUTPUT_DIR)
    _render_user_guide(OUTPUT_DIR / "user_guide.pdf")
    _render_user_guide_docx(OUTPUT_DIR / "user_guide.docx")
    # Run the suites in the background; coverage/JUnit/Test Report land when done.
    _start_coverage_refresh(OUTPUT_DIR)
    return jsonify(_catalogue())


@audit_reports_bp.get("/coverage-status")
def coverage_status():
    """Poll target for the UI while a background coverage refresh runs."""
    with _cov_lock:
        return jsonify({"running": _cov_state["running"], "error": _cov_state["error"]})
