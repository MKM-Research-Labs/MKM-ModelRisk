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
"""Tests for the coding-rule audit PDF builder."""
from __future__ import annotations

from audit.pdf import (REPORTS, STANDALONE_REPORTS, build_audit_tex,
                       build_report_tex, build_test_report_tex, render_audit_pdf,
                       render_report_pdf, render_test_report_pdf)
from src.governance.mrc import pack
from src.governance.mrc.pack import _esc

_CLEAN = {
    "large_source_files": [], "large_web_files": [], "large_test_files": [],
    "hardcoding": [], "embedded_js": [], "init_files": [],
    "init_inventory": [{"path": "pkg/__init__.py", "lines": 6, "reexport": True}],
    "data_access": [], "path_definitions": [], "json_files": [],
    "styling": [], "styling_backlog": [], "undefined_tokens": [],
    "coverage": {"available": True, "line_rate": 0.995, "lines_valid": 1000,
                 "lines_covered": 995, "by_package": []},
    "duplication": {"available": True, "percentage": 0.5, "clones": 3},
}
_FINDINGS = {
    "large_source_files": [{"path": "x.py", "lines": 350}],
    "large_web_files": [{"path": "w.js", "lines": 534}],
    "large_test_files": [],
    "hardcoding": [{"path": "y.py", "line": 4, "kind": "allcaps", "name": "MAXN"}],
    "embedded_js": [{"path": "z.py", "line": 9, "kind": "script", "js_lines": 5}],
    "init_files": [{"path": "p.py", "functions": ["f"], "classes": ["C"]}],
    "init_inventory": [{"path": "p/__init__.py", "lines": 40, "reexport": False},
                       {"path": "q/__init__.py", "lines": 5, "reexport": True}],
    "data_access": [{"path": "d.py", "line": 7, "kind": "sql", "snippet": "SELECT 1 FROM t"}],
    "path_definitions": [{"path": "q.py", "line": 3, "kind": "root_walk",
                          "snippet": "Path(__file__).parents[1]"}],
    "json_files": [{"path": "j.py", "line": 8, "kind": "load",
                    "snippet": "cfg = json.load(fh)"}],
    "styling": [{"path": "a.css", "line": 2, "kind": "asset", "snippet": "#1976d2"}],
    "styling_backlog": [{"path": "b.js", "line": 5, "kind": "js", "snippet": "#f57c00"}],
    "undefined_tokens": [{"path": "a.css", "line": 3, "kind": "undefined_token",
                          "snippet": "--ghost"}],
    "coverage": {"available": True, "line_rate": 0.90, "lines_valid": 200,
                 "lines_covered": 180,
                 "by_package": [{"package": "src.models", "rate": 60.0, "valid": 50,
                                 "covered": 30, "gap": 20}]},
    "duplication": {"available": False},
}


def test_build_audit_tex_clean():
    tex = build_audit_tex(_CLEAN, "2026-06-25")
    assert "Coding-Rule Audit Report" in tex
    assert "2026-06-25" in tex
    assert "No findings." in tex
    assert "0.5\\%" in tex
    assert "99.5\\% achieved" in tex          # R3 achieved coverage in summary
    assert tex.strip().endswith("\\end{document}")


def test_summary_table_lists_every_rule_in_order():
    tex = build_audit_tex(_CLEAN, "2026-06-25")
    # One row per audited rule, in ascending order. R5 (copyright headers) is
    # absent by design: it is checked by hand, not by this audit.
    markers = ["config package", "size limit", "test coverage", "init",
               "src/database", "embedded in", "duplicated code", "config/theme"]
    positions = [tex.index(m) for m in markers]
    assert positions == sorted(positions)
    assert "Filesystem paths defined only in config" in tex   # R6 path row
    assert "Clean" in tex                    # reported-rule result (no findings)
    assert "Pass" in tex                     # mechanical-rule result


def test_build_audit_tex_with_findings():
    tex = build_audit_tex(_FINDINGS, "2026-06-25")
    assert "x.py" in tex and "350" in tex
    assert "w.js" in tex and "534" in tex     # R2 large web file (reported)
    assert "y.py" in tex
    assert "z.py" in tex and "script" in tex
    assert "d.py" in tex                      # R6 data-access finding
    assert "q.py" in tex                      # R6 path-definition finding
    assert "src.models" in tex and "60.0\\%" in tex   # R3 below-threshold package
    assert "not measured" in tex


def test_render_audit_pdf(monkeypatch):
    monkeypatch.setattr(pack, "compile_tex", lambda tex, assets=None: b"%PDF-stub")
    assert render_audit_pdf(_CLEAN, "2026-06-25") == b"%PDF-stub"


def test_one_report_per_audit_rule():
    # Every audited rule gets its own standalone report, each with a stable
    # filename. R5 has none — the copyright-header check is not part of the audit.
    rules = {spec["filename"].split("_")[1] for spec in REPORTS}
    assert rules == {"r1", "r2", "r3", "r4", "r6", "r7", "r8", "r10"}
    assert all(spec["filename"].endswith(".pdf") for spec in REPORTS)
    assert len({spec["filename"] for spec in REPORTS}) == len(REPORTS)


def test_each_report_builds_a_standalone_document():
    for spec in REPORTS:
        tex = build_report_tex(_FINDINGS, spec, "2026-06-25")
        assert tex.startswith("\\documentclass")
        assert tex.strip().endswith("\\end{document}")
        assert _esc(spec["title"]) in tex             # page title rendered
        assert _esc(spec["subtitle"]) in tex          # page subtitle rendered


def test_per_rule_report_carries_only_its_own_findings():
    # The R1 report shows the hardcoding finding but not, say, the data-access one.
    r1 = next(s for s in REPORTS if s["filename"].startswith("audit_r1"))
    tex = build_report_tex(_FINDINGS, r1, "2026-06-25")
    assert "y.py" in tex and "MAXN" in tex
    assert "d.py" not in tex

    r3 = next(s for s in REPORTS if s["filename"].startswith("audit_r3"))
    cov_tex = build_report_tex(_FINDINGS, r3, "2026-06-25")
    assert "src.models" in cov_tex and "60.0\\%" in cov_tex


def test_render_report_pdf_compiles_a_spec(monkeypatch):
    monkeypatch.setattr(pack, "compile_tex", lambda tex, assets=None: b"%PDF-rule")
    assert render_report_pdf(_CLEAN, REPORTS[0], "2026-06-25") == b"%PDF-rule"


def test_json_files_standalone_report_renders_its_findings():
    spec = next(s for s in STANDALONE_REPORTS if s["filename"] == "json_files_report.pdf")
    tex = build_report_tex(_FINDINGS, spec, "2026-06-25")
    assert "j.py" in tex and "load" in tex
    assert _esc(spec["title"]) in tex
    # Standalone reports are not folded into the consolidated summary table.
    assert "j.py" not in build_audit_tex(_FINDINGS, "2026-06-25")


def test_test_report_summarises_suites_and_coverage():
    results = {"unit": {"tests": 500, "failures": 0, "errors": 0, "skipped": 2,
                        "passed": 498, "time": 60.0}, "e2e": None}
    tex = build_test_report_tex(results, _CLEAN["coverage"], "2026-06-25")
    assert "Test Report" in tex
    assert "500" in tex and "PASS" in tex     # unit suite counted + passing
    assert "not run" in tex                    # e2e did not run
    assert "99.50\\%" in tex                   # coverage line rate


def test_test_report_marks_failures_and_missing_coverage():
    results = {"unit": {"tests": 10, "failures": 2, "errors": 1, "skipped": 0,
                        "passed": 7, "time": 1.0}, "e2e": None}
    tex = build_test_report_tex(results, {"available": False}, "2026-06-25")
    assert "FAIL" in tex
    assert "Coverage was not measured" in tex


def test_render_test_report_pdf_compiles(monkeypatch):
    monkeypatch.setattr(pack, "compile_tex", lambda tex, assets=None: b"%PDF-test")
    out = render_test_report_pdf({"unit": None, "e2e": None}, {"available": False},
                                 "2026-06-25")
    assert out == b"%PDF-test"
