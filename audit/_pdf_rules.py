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
"""What each coding rule says about itself, as LaTeX.

One body builder per audited rule, plus the registries naming them. These are the
single source of truth for rule content: the standalone per-rule PDFs and the
consolidated report both compose their bodies from here, so a rule explained once
is explained the same way in both.

Kept apart from ``audit.pdf`` -- which is about assembling and compiling a
document -- because the two change for different reasons. A new rule adds a body
and a registry entry here and touches nothing there; a change to the house style
or the LaTeX toolchain is the reverse.
"""
from __future__ import annotations

from config.audit import COVERAGE_MINIMUM
from src.governance.latex import _section, _table

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
        + _findings_section("R10 — Colour literals in ungated asset types (reported)",
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


__all__ = ["REPORTS", "STANDALONE_REPORTS", "REPORT_LABELS", "_result", "_reported"]
