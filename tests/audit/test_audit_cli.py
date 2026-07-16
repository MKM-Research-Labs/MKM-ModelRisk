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
"""Audit CLI: the consolidated ``python -m audit`` report."""
from __future__ import annotations

import json

import audit.__main__ as cli
from audit.__main__ import build_report, main, write_init_audit_json
from src.governance.mrc import pack

_SECTIONS = {
    "large_source_files", "large_web_files", "large_test_files", "hardcoding",
    "embedded_js", "init_files", "init_inventory", "headers", "licence_notices",
    "data_access", "path_definitions",
    "coverage", "duplication", "json_files",
}


def test_build_report_has_every_section(monkeypatch):
    monkeypatch.setattr(cli, "duplication_report", lambda: {"available": False})
    assert set(build_report()) == _SECTIONS


def test_main_prints_report_and_returns_code(monkeypatch, capsys):
    monkeypatch.setattr(cli, "duplication_report", lambda: {"available": False})
    code = main()
    out = capsys.readouterr().out
    assert "coding-rule audit" in out
    assert "pyproject fail_under" in out       # R3 line, live or gate-only
    assert "jscpd not installed" in out
    assert code in (0, 1)


def test_help_flag_prints_usage_and_exits_zero(capsys):
    assert main(["--help"]) == 0
    assert "usage: python -m audit" in capsys.readouterr().out


def test_pdf_flag_writes_the_full_report_set(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(cli, "AUDIT_OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(pack, "compile_tex", lambda tex, assets=None: b"%PDF stub")
    monkeypatch.setattr(cli, "duplication_report", lambda: {"available": False})

    main(["--pdf"])
    out = capsys.readouterr().out
    names = sorted(p.name for p in tmp_path.glob("*.pdf"))
    assert "coding_rule_audit.pdf" in names
    assert "json_files_report.pdf" in names          # standalone JSON-file audit
    assert sum(n.startswith("audit_r") for n in names) == 9
    assert "Generated" in out and str(tmp_path) in out


def test_write_init_audit_json_exports_findings(tmp_path, monkeypatch):
    monkeypatch.setattr(cli, "duplication_report", lambda: {"available": False})
    report = build_report()
    dest = write_init_audit_json(report, tmp_path)
    assert dest.name == "init_audit_results.json"
    payload = json.loads(dest.read_text())
    assert payload["count"] == len(report["init_files"])
    assert payload["findings"] == report["init_files"]


def test_pdf_flag_reports_missing_engine(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(cli, "AUDIT_OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(cli, "duplication_report", lambda: {"available": False})

    def _no_engine(tex, assets=None):
        raise pack.TectonicNotFound("tectonic not found")

    monkeypatch.setattr(pack, "compile_tex", _no_engine)
    code = main(["--pdf"])
    assert code == 1
    assert "PDF generation skipped" in capsys.readouterr().out
    assert not list(tmp_path.glob("*.pdf"))          # nothing half-written
