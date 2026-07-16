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
"""Tests for the audit-reports API (list, generate, serve)."""
from __future__ import annotations

import audit.__main__ as audit_main
import src.web.api_audit_reports as mod
from src.governance.mrc import pack
from tests.web.conftest import HEADERS


def _stub_pdf(tex, assets=None):
    return b"%PDF-1.4 stub"


def test_list_empty_when_no_output_dir(client, tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "OUTPUT_DIR", tmp_path / "audit")
    assert client.get("/api/audit-reports").get_json() == []


def test_generate_then_list_and_view(client, tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "OUTPUT_DIR", tmp_path / "audit")
    monkeypatch.setattr(pack, "compile_tex", _stub_pdf)             # no tectonic
    monkeypatch.setattr(audit_main, "duplication_report", lambda: {"available": False})  # no jscpd
    monkeypatch.setattr(mod, "_render_user_guide", lambda dest: dest.write_bytes(b"%PDF ug"))  # no pandoc
    monkeypatch.setattr(mod, "_start_coverage_refresh", lambda output_dir: True)  # no test-suite run

    generated = client.post("/api/audit-reports/generate", headers=HEADERS)
    assert generated.status_code == 200
    names = {r["filename"] for r in generated.get_json()}
    assert {"coding_rule_audit.pdf", "model_risk_report.pdf", "user_guide.pdf"} <= names
    # One standalone PDF per audit rule R1–R8 is generated in the same click.
    assert {"audit_r1_hardcoded_parameters.pdf", "audit_r3_test_coverage.pdf",
            "audit_r8_duplicate_code.pdf"} <= names
    assert sum(n.startswith("audit_r") for n in names) == 9

    catalogue = client.get("/api/audit-reports").get_json()
    labels = {r["label"] for r in catalogue}
    assert {"Coding-Rule Audit", "User Guide", "R1 — Hardcoded parameters",
            "R3 — Test coverage"} <= labels
    assert all(r["size"] > 0 and r["modified"] for r in catalogue)

    served = client.get("/api/audit-reports/coding_rule_audit.pdf")
    assert served.status_code == 200 and served.data.startswith(b"%PDF")


def test_generate_returns_503_without_tectonic(client, tmp_path, monkeypatch):
    # The engine is an optional system dependency: when it's absent, generation
    # must fail with an actionable 503, not an unhandled 500 stack trace.
    out = tmp_path / "audit"
    monkeypatch.setattr(mod, "OUTPUT_DIR", out)
    monkeypatch.setattr(pack.shutil, "which", lambda _name: None)          # no tectonic
    monkeypatch.setattr(audit_main, "duplication_report", lambda: {"available": False})

    res = client.post("/api/audit-reports/generate", headers=HEADERS)
    assert res.status_code == 503
    assert "tectonic" in res.get_json()["error"]
    assert not list(out.glob("*.pdf"))          # nothing half-written


def test_user_guide_skipped_without_pandoc(tmp_path, monkeypatch):
    monkeypatch.setattr(mod.shutil, "which", lambda _name: None)
    dest = tmp_path / "user_guide.pdf"
    mod._render_user_guide(dest)
    assert not dest.exists()


def test_user_guide_runs_pandoc_when_available(tmp_path, monkeypatch):
    monkeypatch.setattr(mod.shutil, "which", lambda _name: "/usr/bin/pandoc")
    calls = []
    monkeypatch.setattr(mod.subprocess, "run", lambda cmd, **kw: calls.append(cmd))
    mod._render_user_guide(tmp_path / "user_guide.pdf")
    assert calls and calls[0][0] == "pandoc" and "--pdf-engine=tectonic" in calls[0]


def test_coverage_refresh_rebuilds_reports_and_clears_running(tmp_path, monkeypatch):
    # Skip the ~1-min suite; the refresh still writes the Test Report and rebuilds
    # the coverage-aware reports (R3 + consolidated).
    monkeypatch.setattr(mod, "run_test_suite", lambda output_dir: {"unit": None, "e2e": None})
    monkeypatch.setattr(pack, "compile_tex", _stub_pdf)
    monkeypatch.setattr(audit_main, "duplication_report", lambda: {"available": False})
    monkeypatch.setitem(mod._cov_state, "running", True)

    mod._run_coverage_and_rebuild(tmp_path)

    assert mod._cov_state["running"] is False and mod._cov_state["error"] is None
    assert (tmp_path / "test_report.pdf").exists()
    assert (tmp_path / "audit_r3_test_coverage.pdf").exists()
    assert (tmp_path / "coding_rule_audit.pdf").exists()


def test_coverage_refresh_records_error(tmp_path, monkeypatch):
    def _boom(output_dir):
        raise RuntimeError("pytest exploded")

    monkeypatch.setattr(mod, "run_test_suite", _boom)
    monkeypatch.setitem(mod._cov_state, "running", True)
    mod._run_coverage_and_rebuild(tmp_path)
    assert mod._cov_state["running"] is False
    assert "pytest exploded" in mod._cov_state["error"]


def test_start_coverage_refresh_spawns_once_and_guards(tmp_path, monkeypatch):
    # Starts a background refresh when idle; refuses to stack a second one.
    spawned = []

    class _FakeThread:
        def __init__(self, target, args, daemon):
            self.args = args

        def start(self):
            spawned.append(self.args)

    monkeypatch.setattr(mod.threading, "Thread", _FakeThread)
    monkeypatch.delenv(mod.SUITE_ACTIVE_ENV, raising=False)     # not nested here
    monkeypatch.setitem(mod._cov_state, "running", False)

    assert mod._start_coverage_refresh(tmp_path) is True
    assert mod._cov_state["running"] is True and spawned == [(tmp_path,)]
    # Already running → no second thread.
    assert mod._start_coverage_refresh(tmp_path) is False
    assert len(spawned) == 1
    monkeypatch.setitem(mod._cov_state, "running", False)      # restore for others


def test_start_coverage_refresh_declines_when_nested_in_a_suite(tmp_path, monkeypatch):
    # A generate fired from inside a running suite must not spawn another suite.
    monkeypatch.setenv(mod.SUITE_ACTIVE_ENV, "1")
    monkeypatch.setitem(mod._cov_state, "running", False)
    assert mod._start_coverage_refresh(tmp_path) is False
    assert mod._cov_state["running"] is False          # never flipped on


def test_coverage_status_endpoint_shape(client):
    body = client.get("/api/audit-reports/coverage-status").get_json()
    assert set(body) == {"running", "error"}


def test_catalogue_lists_non_pdf_artefacts_and_coverage_html(client, tmp_path, monkeypatch):
    out = tmp_path / "audit"
    (out / "coverage").mkdir(parents=True)
    (out / "coding_rule_audit.pdf").write_bytes(b"%PDF stub")
    (out / "junit.xml").write_text("<testsuite/>")
    (out / "init_audit_results.json").write_text("{}")
    (out / "coverage" / "index.html").write_text("<html>cov</html>")
    monkeypatch.setattr(mod, "OUTPUT_DIR", out)

    catalogue = client.get("/api/audit-reports").get_json()
    by_name = {r["filename"]: r for r in catalogue}
    assert by_name["junit.xml"]["type"] == "XML"
    assert by_name["junit.xml"]["label"] == "JUnit Results"
    assert by_name["init_audit_results.json"]["type"] == "JSON"
    # The coverage HTML directory is surfaced as one card that opens its own page.
    by_label = {r["label"]: r for r in catalogue}
    cov = by_label[mod.COVERAGE_HTML_LABEL]
    assert cov["type"] == "HTML" and cov["href"] == "coverage"


def test_serve_coverage_index_and_assets(client, tmp_path, monkeypatch):
    out = tmp_path / "audit"
    (out / "coverage").mkdir(parents=True)
    (out / "coverage" / "index.html").write_text("<html>cov index</html>")
    (out / "coverage" / "style.css").write_text("body{}")
    monkeypatch.setattr(mod, "OUTPUT_DIR", out)

    assert b"cov index" in client.get("/api/audit-reports/coverage").data
    assert b"body{}" in client.get("/api/audit-reports/coverage/style.css").data


def test_serve_coverage_404_when_absent(client, tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "OUTPUT_DIR", tmp_path / "audit")
    assert client.get("/api/audit-reports/coverage").status_code == 404
    assert client.get("/api/audit-reports/coverage/style.css").status_code == 404


def test_serve_non_pdf_downloads_as_attachment(client, tmp_path, monkeypatch):
    out = tmp_path / "audit"
    out.mkdir()
    (out / "junit.xml").write_text("<testsuite/>")
    monkeypatch.setattr(mod, "OUTPUT_DIR", out)
    res = client.get("/api/audit-reports/junit.xml")
    assert res.status_code == 200
    assert "attachment" in res.headers.get("Content-Disposition", "")


def test_serve_missing_dir_is_404(client, tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "OUTPUT_DIR", tmp_path / "audit")
    assert client.get("/api/audit-reports/anything.pdf").status_code == 404


def test_serve_unknown_file_is_404(client, tmp_path, monkeypatch):
    out = tmp_path / "audit"
    out.mkdir()
    monkeypatch.setattr(mod, "OUTPUT_DIR", out)
    assert client.get("/api/audit-reports/nope.pdf").status_code == 404
