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
"""The blueprint, the directory it serves, and the catalogue of what is in it.

Shared by every module in this package, in the way ``api_mrc/_bp`` is: the route
modules attach to ``audit_reports_bp``, and both of them read ``OUTPUT_DIR`` from
here rather than importing the value, so a test pointing this module at a temporary
directory moves the whole package with it.
"""
from __future__ import annotations

from datetime import datetime

from flask import Blueprint

from audit.pdf import REPORT_LABELS
from config.audit import (AUDIT_OUTPUT_DIR, AUDIT_REPORT_LABELS,
                          COVERAGE_HTML_DIRNAME, COVERAGE_HTML_LABEL,
                          DEFAULT_REPORT_GROUP, USER_FOCUSED_REPORTS,
                          USER_REPORT_GROUP)

# Module-level so tests can point it at a temporary directory.
OUTPUT_DIR = AUDIT_OUTPUT_DIR

audit_reports_bp = Blueprint("audit_reports", __name__, url_prefix="/api/audit-reports")


# Filename -> human label: the fixed reports plus every generated per-rule PDF.
_LABELS = {**AUDIT_REPORT_LABELS, **REPORT_LABELS}

# File extension -> short type badge shown in the tab.
_TYPE_LABELS = {".pdf": "PDF", ".xml": "XML", ".json": "JSON",
                ".txt": "TXT", ".html": "HTML"}


def entry(path) -> dict:
    """Catalogue row for one artefact file ``path``, tagged with its sub-tab group."""
    stat = path.stat()
    ext = path.suffix.lower()
    return {
        "filename": path.name,
        "label": _LABELS.get(path.name, path.stem.replace("_", " ").title()),
        "group": (USER_REPORT_GROUP if path.name in USER_FOCUSED_REPORTS
                  else DEFAULT_REPORT_GROUP),
        "type": _TYPE_LABELS.get(ext, ext.lstrip(".").upper() or "FILE"),
        "size": stat.st_size,
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
    }


def catalogue() -> list[dict]:
    """Every artefact in the output dir, plus the browsable coverage HTML report."""
    if not OUTPUT_DIR.is_dir():
        return []
    reports = [entry(path)
               for path in sorted(OUTPUT_DIR.iterdir())
               if path.is_file() and not path.name.startswith(".")]
    cov_index = OUTPUT_DIR / COVERAGE_HTML_DIRNAME / "index.html"
    if cov_index.is_file():
        stat = cov_index.stat()
        reports.append({
            "filename": f"{COVERAGE_HTML_DIRNAME}/index.html",
            "label": COVERAGE_HTML_LABEL,
            "group": DEFAULT_REPORT_GROUP,      # R3 evidence, like the XML beside it
            "type": "HTML",
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
            "href": "coverage",         # served by the coverage route, not the file route
        })
    return reports
