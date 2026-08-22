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

Two shapes are produced from the same per-rule body builders: one standalone
PDF per audit function (see ``REPORTS``), each surfaced individually in the
Audit Reports tab, plus a consolidated ``coding_rule_audit.pdf`` that carries
the summary table followed by every rule's findings.
"""
from __future__ import annotations

from config.audit import COVERAGE_MINIMUM
from src.governance.latex import (
    _section, _table, front_matter, history_page, logo_asset, preamble,
)
from src.governance.mrc import pack

from audit.coverage import low_coverage_packages


def _findings_section(title: str, findings: list, headers: list[str], row_of) -> str:
    if not findings:
        return _section(title, "No findings.\\par\\medskip\n")
    return _section(title, _table(headers, [row_of(f) for f in findings]))


def _result(findings: list) -> str:
    """A pass/fail cell for a mechanically-checked rule."""
    return "Pass" if not findings else str(len(findings)) + " finding(s)"


def _reported(findings: list) -> str:
    """A cell for a reported (non-gating) rule: clean, or a count for visibility."""
    return "Clean" if not findings else str(len(findings)) + " reported"


# --- per-rule body builders --------------------------------------------------
# Each takes the full audit ``report`` dict and returns LaTeX for that one rule.
# They are the single source of truth: both the standalone per-rule PDFs and the
# consolidated report compose their bodies from these.

def _hardcoding_body(report: dict) -> str:
    return _findings_section("R1 — Hardcoded parameters", report["hardcoding"],
                             ["File", "Line", "Kind", "Name"],
                             lambda f: [f["path"], f["line"], f["kind"], f["name"]])


def _styling_body(report: dict) -> str:
    return (
        _findings_section("R10 — Colour literals outside config/theme", report["styling"],
                          ["File", "Line", "Kind", "Colour"],
                          lambda f: [f["path"], f["line"], f["kind"], f["snippet"]])
        + _findings_section("R10 — Undefined design tokens", report["undefined_tokens"],
                            ["File", "Line", "Token"],
                            lambda f: [f["path"], f["line"], f["snippet"]])
        + _findings_section("R10 — Colour literals in JavaScript (reported)",
                            report["styling_backlog"], ["File", "Line", "Colour"],
                            lambda f: [f["path"], f["line"], f["snippet"]])
    )


def _large_files_body(report: dict) -> str:
    return (
        _findings_section("R2 — Large source files (>300 lines)", report["large_source_files"],
                          ["File", "Lines"], lambda f: [f["path"], f["lines"]])
        + _findings_section("R2 — Large test files (>400 lines)", report["large_test_files"],
                            ["File", "Lines"], lambda f: [f["path"], f["lines"]])
        + _findings_section("R2 — Large web files (>300 lines, reported)", report["large_web_files"],
                            ["File", "Lines"], lambda f: [f["path"], f["lines"]])
    )


def _coverage_body(report: dict) -> str:
    cov = report.get("coverage") or {}
    if not cov.get("available"):
        return ("Coverage was not measured (no coverage.xml present). The gate is "
                "enforced by pyproject \\texttt{fail\\_under} at "
                + str(COVERAGE_MINIMUM) + "\\%.\\par\\medskip\n")
    pct = cov["line_rate"] * 100
    intro = ("Overall line coverage: \\textbf{" + f"{pct:.2f}" + "\\%} ("
             + f"{cov['lines_covered']:,}" + " of " + f"{cov['lines_valid']:,}"
             + " lines). Gate " + str(COVERAGE_MINIMUM) + "\\%.\\par\\medskip\n")
    return intro + _findings_section(
        "R3 — Packages below " + str(COVERAGE_MINIMUM) + "% coverage (reported)",
        low_coverage_packages(cov, COVERAGE_MINIMUM),
        ["Package", "Coverage", "Lines", "Covered", "Gap"],
        lambda r: [r["package"], f"{r['rate']:.1f}%", r["valid"], r["covered"], r["gap"]])


def _init_files_body(report: dict) -> str:
    inventory = report.get("init_inventory", [])
    embedded = [item for item in inventory if not item["reexport"]]
    # Underscores are escaped: these run as literal text, not through _esc.
    intro = ("Every package \\texttt{\\_\\_init\\_\\_.py} should be aggregate-only — a "
             "docstring, imports and \\texttt{\\_\\_all\\_\\_}, with no functions, classes "
             "or module-level logic. All " + str(len(inventory)) + " first-party "
             "\\texttt{\\_\\_init\\_\\_.py} files are listed below; " + str(len(embedded))
             + " contain code.\\par\\medskip\n")
    return intro + _findings_section(
        "R4 — __init__.py inventory", inventory,
        ["File", "Lines", "Re-export only"],
        lambda f: [f["path"], f["lines"], "Yes" if f["reexport"] else "No"])


def _data_access_body(report: dict) -> str:
    return _findings_section(
        "R6 — Data access outside src/database (reported)", report["data_access"],
        ["File", "Line", "Kind", "Snippet"],
        lambda f: [f["path"], f["line"], f["kind"], f["snippet"]])


def _path_definitions_body(report: dict) -> str:
    return _findings_section(
        "R6 — Path definitions outside config (reported)", report["path_definitions"],
        ["File", "Line", "Kind", "Snippet"],
        lambda f: [f["path"], f["line"], f["kind"], f["snippet"]])


def _embedded_js_body(report: dict) -> str:
    return _findings_section(
        "R7 — Embedded JavaScript / CSS", report["embedded_js"],
        ["File", "Line", "Kind", "JS lines"],
        lambda f: [f["path"], f["line"], f["kind"], f["js_lines"]])


def _duplication_body(report: dict) -> str:
    dup = report["duplication"]
    if not dup.get("available"):
        return "Duplicate-code detection was not run (jscpd not installed).\\par\\medskip\n"
    return _table(["Metric", "Value"], [
        ["Duplication", str(dup["percentage"]) + "%"],
        ["Clones", str(dup["clones"])],
        ["Duplicated lines", str(dup.get("duplicated_lines", "—"))],
    ])


def _json_files_body(report: dict) -> str:
    findings = report.get("json_files", [])
    intro = ("First-party source should persist through the Postgres event store, "
             "not ``.json`` files on disk. Every touch below is migration backlog "
             "(reported, not gated).\\par\\medskip\n")
    return intro + _findings_section(
        "JSON-file I/O under the source tree", findings,
        ["File", "Line", "Kind", "Snippet"],
        lambda f: [f["path"], f["line"], f["kind"], f["snippet"]])


# One standalone report per audit function. ``body`` renders the rule's findings;
# ``title``/``subtitle`` head the page; ``label`` names it in the Audit Reports tab.
REPORTS = [
    {"filename": "audit_r1_hardcoded_parameters.pdf", "label": "R1 — Hardcoded parameters",
     "title": "R1 — Hardcoded Parameters",
     "subtitle": "Parameters live only in the config package", "body": _hardcoding_body},
    {"filename": "audit_r2_large_files.pdf", "label": "R2 — Large files",
     "title": "R2 — Large Files",
     "subtitle": "No file over the size limit (300 source / 400 test lines)",
     "body": _large_files_body},
    {"filename": "audit_r3_test_coverage.pdf", "label": "R3 — Test coverage",
     "title": "R3 — Test Coverage",
     "subtitle": "At least " + str(COVERAGE_MINIMUM) + "% test coverage",
     "body": _coverage_body},
    {"filename": "audit_r4_init_files.pdf", "label": "R4 — __init__.py",
     "title": "R4 — Substantive __init__.py",
     "subtitle": "No functions or logic in __init__.py", "body": _init_files_body},
    {"filename": "audit_r6_data_access.pdf", "label": "R6 — Data access",
     "title": "R6 — Data Access",
     "subtitle": "Data store reached only through src/database", "body": _data_access_body},
    {"filename": "audit_r6_path_definitions.pdf", "label": "R6 — Path definitions",
     "title": "R6 — Path Definitions",
     "subtitle": "Filesystem paths defined only in config", "body": _path_definitions_body},
    {"filename": "audit_r7_embedded_js.pdf", "label": "R7 — Embedded JS/CSS",
     "title": "R7 — Embedded JavaScript / CSS",
     "subtitle": "No JavaScript or CSS embedded in .py files", "body": _embedded_js_body},
    {"filename": "audit_r8_duplicate_code.pdf", "label": "R8 — Duplicate code",
     "title": "R8 — Duplicate Code",
     "subtitle": "No duplicated code; shared logic extracted", "body": _duplication_body},
    {"filename": "audit_r10_styling.pdf", "label": "R10 — Styling",
     "title": "R10 — Styling",
     "subtitle": "Colours live only in config/theme, and every token resolves",
     "body": _styling_body},
]

# Standalone evidence reports rendered next to the R1–R8 set but kept out of the
# consolidated audit's summary table (they are not one of the numbered rules).
STANDALONE_REPORTS = [
    {"filename": "json_files_report.pdf", "label": "JSON-File Audit",
     "title": "JSON-File Audit",
     "subtitle": "Source persists through Postgres, not .json files",
     "body": _json_files_body},
]

# Filename -> Audit-Reports-tab label, for every generated per-rule/standalone PDF.
REPORT_LABELS = {spec["filename"]: spec["label"]
                 for spec in (*REPORTS, *STANDALONE_REPORTS)}


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
    oversize = report["large_source_files"] + report["large_test_files"]
    return _table(
        ["Rule", "Requirement", "Result"],
        [
            ["R1", "Parameters live only in the config package", _result(report["hardcoding"])],
            ["R2", "No file over the size limit (300 source / 400 test lines)", _result(oversize)],
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
            ["R10", "Colour literals still to convert (JavaScript)",
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
