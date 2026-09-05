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
"""Console coding-rule audit report: ``python -m audit``."""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

from config.audit import AUDIT_OUTPUT_DIR, COVERAGE_MINIMUM, INIT_AUDIT_JSON_NAME
from src.governance.mrc.pack import TectonicNotFound

from audit.coverage import coverage_summary, low_coverage_packages
from audit.data_access import data_access_findings
from audit.duplication import duplication_report
from audit.embedded_js import embedded_js_findings
from audit.hardcoding import hardcoding_findings
from audit.init_files import init_file_findings, init_file_inventory
from audit.json_files import json_file_findings
from audit.large_files import large_source_files, large_test_files, large_web_files
from audit.path_definitions import path_definition_findings
from audit.styling import (colour_literal_findings, unconverted_colour_findings,
                           undefined_token_findings)
from audit.pdf import (REPORTS, STANDALONE_REPORTS, render_audit_pdf,
                       render_report_pdf)

_USAGE = ("usage: python -m audit [--pdf]\n\n"
          "  --pdf   also render the audit reports (one PDF per rule plus a consolidated\n"
          "          overview) into the audit output directory")


def _print_section(title: str, findings: list[dict], formatter) -> int:
    mark = "OK " if not findings else "!! "
    print(f"\n{mark}{title} — {len(findings)} finding(s)")
    for item in findings:
        print("     " + formatter(item))
    return len(findings)


def _print_init_inventory(inventory: list[dict], substantive: list[dict]) -> int:
    """List every __init__.py with its length and re-export verdict (R4).

    The full inventory is shown for visibility; the gated count is the number of
    substantive files (those defining functions or classes).
    """
    not_reexport = [item for item in inventory if not item["reexport"]]
    mark = "OK " if not not_reexport else "!! "
    print(f"\n{mark}R4 __init__.py — {len(inventory)} file(s), "
          f"{len(not_reexport)} with embedded code")
    for item in inventory:
        flag = "re-export" if item["reexport"] else "HAS CODE "
        print(f"     {item['lines']:>4} lines  {flag}  {item['path']}")
    return len(substantive)


def build_report() -> dict:
    """Collect every audit's findings into one dict (used by tests and the CLI)."""
    return {
        "large_source_files": large_source_files(),
        "large_web_files": large_web_files(),
        "large_test_files": large_test_files(),
        "hardcoding": hardcoding_findings(),
        "embedded_js": embedded_js_findings(),
        "init_files": init_file_findings(),
        "init_inventory": init_file_inventory(),
        "data_access": data_access_findings(),
        "path_definitions": path_definition_findings(),
        "coverage": coverage_summary(),
        "duplication": duplication_report(),
        "json_files": json_file_findings(),
        "styling": colour_literal_findings(),
        "styling_backlog": unconverted_colour_findings(),
        "undefined_tokens": undefined_token_findings(),
    }


def write_audit_reports(report: dict, as_of: str, output_dir: Path,
                        errors: list | None = None) -> list[Path]:
    """Render every per-rule PDF plus the consolidated overview into ``output_dir``.

    Shared by the CLI ``--pdf`` flag and the Audit Reports web endpoint so both
    emit exactly the same set. Returns the paths that were written successfully.

    ``TectonicNotFound`` always propagates — the LaTeX engine is missing, so no
    report can be produced at all. Any *other* per-report failure (a one-off
    tectonic compile error, a bad glyph in a finding, …) is handled per
    ``errors``: when it is ``None`` (the CLI default) the exception propagates as
    before; when a list is supplied the failure is appended as a
    ``(filename, message)`` pair and the remaining reports are still written — so
    a single failing report can no longer leave every later report stale.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    written = []
    specs = [*REPORTS, *STANDALONE_REPORTS,
             {"filename": "coding_rule_audit.pdf", "consolidated": True}]
    for spec in specs:
        dest = output_dir / spec["filename"]
        try:
            pdf = (render_audit_pdf(report, as_of) if spec.get("consolidated")
                   else render_report_pdf(report, spec, as_of))
            dest.write_bytes(pdf)
            written.append(dest)
        except TectonicNotFound:
            raise
        except Exception as exc:                 # noqa: BLE001 — recorded, not swallowed
            if errors is None:
                raise
            errors.append((spec["filename"], str(exc)))
    return written


def write_init_audit_json(report: dict, output_dir: Path) -> Path:
    """Emit the machine-readable ``__init__`` audit results next to the PDFs."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    dest = output_dir / INIT_AUDIT_JSON_NAME
    payload = {"findings": report["init_files"], "count": len(report["init_files"])}
    dest.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return dest


def _write_pdfs(report: dict) -> int:
    """Render the audit PDFs for ``--pdf``; return a process exit code."""
    try:
        written = write_audit_reports(report, date.today().isoformat(), AUDIT_OUTPUT_DIR)
    except TectonicNotFound as exc:
        print(f"\n!! PDF generation skipped — {exc}")
        return 1
    print(f"\nGenerated {len(written)} PDF(s) in {AUDIT_OUTPUT_DIR}:")
    for path in written:
        print("     " + path.name)
    return 0


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else list(argv)
    if "-h" in argv or "--help" in argv:
        print(_USAGE)
        return 0
    report = build_report()
    print("MKM-ModelRisk — coding-rule audit")
    print("=" * 50)
    total = 0
    total += _print_section("R1 hardcoded parameters", report["hardcoding"],
                            lambda f: f"{f['path']}:{f['line']}  {f['kind']} {f['name']}")
    total += _print_section("R2 large source files (>300)", report["large_source_files"],
                            lambda f: f"{f['lines']:>4}  {f['path']}")
    total += _print_section("R2 large test files (>400)", report["large_test_files"],
                            lambda f: f"{f['lines']:>4}  {f['path']}")
    total += _print_init_inventory(report["init_inventory"], report["init_files"])
    total += _print_section("R7 embedded JavaScript / CSS", report["embedded_js"],
                            lambda f: f"{f['path']}:{f['line']}  {f['kind']} ({f['js_lines']} js lines)")
    total += _print_section("R10 colour literals outside config/theme", report["styling"],
                            lambda f: f"{f['path']}:{f['line']}  {f['kind']}  {f['snippet']}")
    total += _print_section("R10 undefined design tokens", report["undefined_tokens"],
                            lambda f: f"{f['path']}:{f['line']}  {f['snippet']}")
    total += _print_section("R2 large web files (>300)", report["large_web_files"],
                            lambda f: f"{f['lines']:>4}  {f['path']}")
    # Reported (non-gating) sections — visibility only, not counted in ``total``.
    _print_section("R6 data access outside src/database (reported)", report["data_access"],
                   lambda f: f"{f['path']}:{f['line']}  {f['kind']}  {f['snippet']}")
    _print_section("R6 path definitions outside config (reported)", report["path_definitions"],
                   lambda f: f"{f['path']}:{f['line']}  {f['kind']}  {f['snippet']}")
    _print_section("R6 .json file I/O under source (reported)", report["json_files"],
                   lambda f: f"{f['path']}:{f['line']}  {f['kind']}  {f['snippet']}")
    _print_section("R10 colour literals in ungated asset types (reported)",
                   report["styling_backlog"],
                   lambda f: f"{f['path']}:{f['line']}  {f['snippet']}")
    cov = report["coverage"]
    if cov["available"]:
        pct = cov["line_rate"] * 100
        print(f"\n.. R3 coverage — {pct:.2f}% ({cov['lines_covered']:,} of "
              f"{cov['lines_valid']:,} lines); gate {COVERAGE_MINIMUM}% via pyproject fail_under")
        for r in low_coverage_packages(cov):
            print(f"     {r['rate']:5.1f}%  {r['package']}  (gap {r['gap']})")
    else:
        print(f"\n.. R3 — Coverage gate enforced at {COVERAGE_MINIMUM}% via pyproject "
              "fail_under (coverage.xml not found — run pytest --cov --cov-report=xml)")
    dup = report["duplication"]
    if dup.get("available"):
        print(f".. R8 duplicate code — {dup['percentage']}% ({dup['clones']} clones, "
              f"{dup['duplicated_lines']} lines)")
    else:
        print(".. R8 duplicate code — jscpd not installed, skipped")
    print("=" * 50)
    print(f"{'PASS' if total == 0 else 'FINDINGS'}: {total} gated finding(s)")
    exit_code = 1 if total else 0
    if "--pdf" in argv:
        # Render first, then combine: ``exit_code or _write_pdfs(...)`` skipped the
        # rendering entirely whenever the audit had a finding — withholding the
        # reports in exactly the case they are wanted. A failure to render is its
        # own non-zero code, so neither outcome can mask the other.
        exit_code = _write_pdfs(report) or exit_code
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
