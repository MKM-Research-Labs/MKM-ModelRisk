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
"""Render the coding-rule audit findings as PDFs (LaTeX via tectonic).

Two shapes are produced from the same per-rule body builders, which live in
``audit._pdf_rules``: one standalone PDF per audit function (see ``REPORTS``),
each surfaced individually in the Audit Reports tab, plus a consolidated
``coding_rule_audit.pdf`` carrying the summary table followed by every rule's
findings. The test-suite report is built here too -- a different subject, but the
same house style and the same compile step.

``REPORTS``, ``STANDALONE_REPORTS`` and ``REPORT_LABELS`` are re-exported so that
this module stays the one address for PDF generation; callers do not need to know
the rule bodies moved.
"""
from __future__ import annotations

from config.audit import COVERAGE_MINIMUM
from src.governance.latex import (
    _section, _table, front_matter, history_page, logo_asset, preamble,
)
from src.governance.mrc import pack

from audit._pdf_rules import (
    REPORT_LABELS, REPORTS, STANDALONE_REPORTS, _reported, _result,
)



def _document(title: str, subtitle: str, as_of: str, body: str, *,
              logo: bool = False, toc: bool = False) -> str:
    """Wrap a rule body in the shared house style: title page (+ optional Contents),
    the body, then the Document History at the end."""
    return (
        preamble(title) + "\\begin{document}\n"
        + front_matter(title, subtitle, date=as_of, logo=logo, toc=toc)
        + body
        + history_page(as_of, subtitle)
        + "\\end{document}\n"
    )


def _summary_table(report: dict) -> str:
    dup = report["duplication"]
    dup_result = (str(dup["percentage"]) + "% (" + str(dup["clones"]) + " clones)"
                  if dup.get("available") else "not measured")
    cov = report.get("coverage") or {}
    cov_result = (f"{cov['line_rate'] * 100:.1f}% achieved (gate {COVERAGE_MINIMUM}%)"
                  if cov.get("available") else "enforced via pyproject")
    oversize = (report["large_source_files"] + report["large_test_files"]
                + report["large_web_files"])
    return _table(
        ["Rule", "Requirement", "Result"],
        [
            ["R1", "Parameters live only in the config package", _result(report["hardcoding"])],
            ["R2", "No file over the size limit (300 source and web / 400 test lines)",
             _result(oversize)],
            ["R3", "At least " + str(COVERAGE_MINIMUM) + "% test coverage, verified each stage",
             cov_result],
            ["R4", "No functions or logic in __init__.py", _result(report["init_files"])],
            ["R6", "Data store reached only through src/database", _reported(report["data_access"])],
            ["R6", "Filesystem paths defined only in config", _reported(report["path_definitions"])],
            ["R7", "No JavaScript or CSS embedded in .py files", _result(report["embedded_js"])],
            ["R8", "No duplicated code; shared logic extracted", dup_result],
            ["R10", "Colours live only in config/theme", _result(report["styling"])],
            ["R10", "Every design token referenced is defined",
             _result(report["undefined_tokens"])],
            ["R10", "Colour literals in asset types outside the gate",
             _reported(report["styling_backlog"])],
        ],
    )


def build_report_tex(report: dict, spec: dict, as_of: str, *, logo: bool = False) -> str:
    """Pure: render the LaTeX for one standalone per-rule report."""
    return _document(spec["title"], spec["subtitle"], as_of, spec["body"](report), logo=logo)


def build_audit_tex(report: dict, as_of: str, *, logo: bool = False) -> str:
    """Pure: render the consolidated report — summary table + every rule's findings."""
    body = _section("Summary", _summary_table(report))
    for spec in REPORTS:
        body += spec["body"](report)
    return _document("Coding-Rule Audit Report", "Rules R1–R8", as_of, body, logo=logo, toc=True)


def render_report_pdf(report: dict, spec: dict, as_of: str) -> bytes:
    """Build and compile one standalone per-rule report to PDF bytes."""
    assets = logo_asset()
    return pack.compile_tex(build_report_tex(report, spec, as_of, logo=bool(assets)), assets)


def render_audit_pdf(report: dict, as_of: str) -> bytes:
    """Build and compile the consolidated coding-rule audit report to PDF bytes."""
    assets = logo_asset()
    return pack.compile_tex(build_audit_tex(report, as_of, logo=bool(assets)), assets)


def _suite_row(name: str, result: dict | None) -> list:
    """One summary-table row for a test suite; a dash line when it did not run."""
    if not result:
        return [name, "—", "—", "—", "—", "not run"]
    status = "PASS" if result["failures"] == 0 and result["errors"] == 0 else "FAIL"
    return [name, result["tests"], result["failures"], result["errors"],
            result["skipped"], status]


def build_test_report_tex(results: dict, cov: dict, as_of: str, *, logo: bool = False) -> str:
    """Pure: render the model/unit test-summary report (counts + coverage)."""
    body = _section("Test suites", _table(
        ["Suite", "Tests", "Failures", "Errors", "Skipped", "Status"],
        [_suite_row("Unit / model", results.get("unit")),
         _suite_row("End-to-end", results.get("e2e"))]))
    if cov.get("available"):
        pct = cov["line_rate"] * 100
        body += _section("Coverage", _table(
            ["Metric", "Value"],
            [["Line coverage", f"{pct:.2f}%"],
             ["Lines covered", f"{cov['lines_covered']:,}"],
             ["Lines valid", f"{cov['lines_valid']:,}"],
             ["Gate", str(COVERAGE_MINIMUM) + "%"]]))
    else:
        body += ("Coverage was not measured for this run.\\par\\medskip\n")
    return _document("Test Report", "Unit, e2e and coverage evidence", as_of, body, logo=logo, toc=True)


def render_test_report_pdf(results: dict, cov: dict, as_of: str) -> bytes:
    """Build and compile the test-summary report to PDF bytes."""
    assets = logo_asset()
    return pack.compile_tex(build_test_report_tex(results, cov, as_of, logo=bool(assets)), assets)


__all__ = [
    "REPORTS", "STANDALONE_REPORTS", "REPORT_LABELS",
    "build_report_tex", "build_audit_tex", "render_report_pdf", "render_audit_pdf",
    "build_test_report_tex", "render_test_report_pdf",
]
