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
"""Tests for the audit-reports API package (list, generate, serve).

The package keeps its state in ``_bp`` (the output directory) and ``_suite`` (the
background refresh), and the route modules read both through the module object —
so a test points ``_bp.OUTPUT_DIR`` at a temporary directory and the whole package
follows. Where ``generate`` imported a renderer by name, the stub goes on ``gen``:
patching the defining module would not reach the binding it already holds.
"""
from __future__ import annotations

import os

import audit.__main__ as audit_main
from src.web.api_audit_reports import _bp, _guides, _suite
from src.web.api_audit_reports import generate as gen
from config.reporting import DOCUMENT_COLOUR_INCLUDE
from config.theme import BRAND
from src.governance.latex_style import colour_definitions, latex_hex
from src.governance.mrc import pack
from src.governance.mrc.pack import TectonicNotFound
from tests.web.conftest import HEADERS


def _stub_pdf(tex, assets=None):
    return b"%PDF-1.4 stub"


def test_list_empty_when_no_output_dir(client, tmp_path, monkeypatch):
    monkeypatch.setattr(_bp, "OUTPUT_DIR", tmp_path / "audit")
    assert client.get("/api/audit-reports").get_json() == []


def test_generate_then_list_and_view(client, tmp_path, monkeypatch):
    monkeypatch.setattr(_bp, "OUTPUT_DIR", tmp_path / "audit")
    monkeypatch.setattr(pack, "compile_tex", _stub_pdf)             # no tectonic
    monkeypatch.setattr(audit_main, "duplication_report", lambda: {"available": False})  # no jscpd
    monkeypatch.setattr(gen, "render_user_guide", lambda dest: dest.write_bytes(b"%PDF ug"))  # no pandoc
    monkeypatch.setattr(_guides, "compile_tex", _stub_pdf)           # the guides' own compile
    monkeypatch.setattr(_suite, "start_coverage_refresh", lambda output_dir: True)  # no test-suite run

    generated = client.post("/api/audit-reports/generate", headers=HEADERS)
    assert generated.status_code == 200
    payload = generated.get_json()
    assert payload["failures"] == []          # every report rendered
    names = {r["filename"] for r in payload["reports"]}
    assert {"coding_rule_audit.pdf", "model_risk_report.pdf", "user_guide.pdf",
            "integration_guide.pdf"} <= names
    # One standalone PDF per audit rule (R1–R8 and R10) is generated in the same click.
    assert {"audit_r1_hardcoded_parameters.pdf", "audit_r3_test_coverage.pdf",
            "audit_r8_duplicate_code.pdf"} <= names
    assert sum(n.startswith("audit_r") for n in names) == 10

    catalogue = client.get("/api/audit-reports").get_json()
    labels = {r["label"] for r in catalogue}
    assert {"Coding-Rule Audit", "User Guide", "Integration Guide",
            "R1 — Hardcoded parameters", "R3 — Test coverage"} <= labels
    assert all(r["size"] > 0 and r["modified"] for r in catalogue)

    served = client.get("/api/audit-reports/coding_rule_audit.pdf")
    assert served.status_code == 200 and served.data.startswith(b"%PDF")


def test_generate_survives_one_failing_report(client, tmp_path, monkeypatch):
    # A single report blowing up (e.g. a one-off tectonic compile error) must not
    # abort the run: every other report still refreshes and the failure is named
    # under ``failures`` — instead of every report after it silently keeping its
    # previous file and previous date (the "reports are two days old" symptom).
    monkeypatch.setattr(_bp, "OUTPUT_DIR", tmp_path / "audit")
    monkeypatch.setattr(audit_main, "duplication_report", lambda: {"available": False})
    monkeypatch.setattr(gen, "render_user_guide", lambda dest: dest.write_bytes(b"%PDF ug"))
    monkeypatch.setattr(_suite, "start_coverage_refresh", lambda output_dir: True)

    def _one_bad(report, spec, as_of):
        if spec["filename"] == "audit_r6_data_access.pdf":
            raise RuntimeError("tectonic hiccup")
        return b"%PDF-1.4 stub"

    monkeypatch.setattr(audit_main, "render_report_pdf", _one_bad)
    monkeypatch.setattr(audit_main, "render_audit_pdf", lambda report, as_of: b"%PDF-1.4 stub")
    monkeypatch.setattr(gen, "render_report_pdf", lambda *a: b"%PDF-1.4 stub")
    monkeypatch.setattr(gen, "render_completeness_pdf", lambda *a: b"%PDF-1.4 stub")

    res = client.post("/api/audit-reports/generate", headers=HEADERS)
    assert res.status_code == 200
    payload = res.get_json()
    assert [f["file"] for f in payload["failures"]] == ["audit_r6_data_access.pdf"]

    names = {r["filename"] for r in payload["reports"]}
    # Reports after the failing one still refreshed in the same click.
    assert {"audit_r6_path_definitions.pdf", "audit_r8_duplicate_code.pdf",
            "coding_rule_audit.pdf", "model_risk_report.pdf"} <= names
    # The failing report left no partial/stale file with today's date.
    assert not (tmp_path / "audit" / "audit_r6_data_access.pdf").exists()


def test_generate_returns_503_without_tectonic(client, tmp_path, monkeypatch):
    # The engine is an optional system dependency: when it's absent, generation
    # must fail with an actionable 503, not an unhandled 500 stack trace.
    out = tmp_path / "audit"
    monkeypatch.setattr(_bp, "OUTPUT_DIR", out)
    monkeypatch.setattr(pack.shutil, "which", lambda _name: None)          # no tectonic
    monkeypatch.setattr(audit_main, "duplication_report", lambda: {"available": False})

    res = client.post("/api/audit-reports/generate", headers=HEADERS)
    assert res.status_code == 503
    assert "tectonic" in res.get_json()["error"]
    assert not list(out.glob("*.pdf"))          # nothing half-written


def test_user_guide_skipped_without_pandoc(tmp_path, monkeypatch):
    monkeypatch.setattr(_guides.shutil, "which", lambda _name: None)
    dest = tmp_path / "user_guide.pdf"
    _guides.render_user_guide(dest)
    assert not dest.exists()


def test_user_guide_runs_pandoc_then_house_style(tmp_path, monkeypatch):
    # The guide is pandoc'd to a LaTeX fragment, then wrapped in the shared house
    # style and compiled — so it matches every other generated PDF.
    monkeypatch.setattr(_guides.shutil, "which", lambda _name: "/usr/bin/pandoc")
    calls = []

    class _Done:
        stdout = "\\section{Guide}\n"

    monkeypatch.setattr(_guides.subprocess, "run", lambda cmd, **kw: (calls.append(cmd) or _Done()))
    monkeypatch.setattr(_guides, "compile_tex", lambda tex, assets=None: b"%PDF-stub")
    dest = tmp_path / "user_guide.pdf"
    _guides.render_user_guide(dest)
    assert calls and calls[0][0] == "pandoc" and calls[0][-2:] == ["-t", "latex"]
    assert dest.read_bytes() == b"%PDF-stub"


def test_integration_guide_is_drawn_in_the_configured_theme(tmp_path, monkeypatch):
    # The guide is standalone LaTeX, so it carries its own fallback colours. The copy
    # the console publishes must take the deployment's theme instead — otherwise a
    # rebranded install ships a guide in the platform's blue (rule R10).
    sent = {}

    def _capture(tex, assets=None):
        sent["tex"], sent["assets"] = tex, assets
        return b"%PDF-guide"

    monkeypatch.setattr(_guides, "compile_tex", _capture)
    dest = tmp_path / "integration_guide.pdf"
    _guides.render_integration_guide(dest)
    assert dest.read_bytes() == b"%PDF-guide"
    assert "\\documentclass" in sent["tex"]
    supplied = sent["assets"][DOCUMENT_COLOUR_INCLUDE].decode()
    assert supplied == colour_definitions()
    assert latex_hex(BRAND["accent"]) in supplied


def test_integration_guide_skipped_without_tectonic(tmp_path, monkeypatch):
    def _boom(_tex, _assets=None):
        raise TectonicNotFound("no tectonic")

    monkeypatch.setattr(_guides, "compile_tex", _boom)
    dest = tmp_path / "integration_guide.pdf"
    _guides.render_integration_guide(dest)
    assert not dest.exists()


def test_user_guide_skipped_without_tectonic(tmp_path, monkeypatch):
    # pandoc present but tectonic absent: no half-written file, no crash.
    monkeypatch.setattr(_guides.shutil, "which", lambda _name: "/usr/bin/pandoc")

    class _Done:
        stdout = "\\section{Guide}\n"

    monkeypatch.setattr(_guides.subprocess, "run", lambda cmd, **kw: _Done())

    def _boom(_tex, _assets=None):
        raise TectonicNotFound("no tectonic")

    monkeypatch.setattr(_guides, "compile_tex", _boom)
    dest = tmp_path / "user_guide.pdf"
    _guides.render_user_guide(dest)
    assert not dest.exists()


def test_coverage_refresh_rebuilds_reports_and_clears_running(tmp_path, monkeypatch):
    # Skip the ~1-min suite; the refresh still writes the Test Report and rebuilds
    # the coverage-aware reports (R3 + consolidated).
    monkeypatch.setattr(_suite, "run_test_suite", lambda output_dir: {"unit": None, "e2e": None})
    monkeypatch.setattr(pack, "compile_tex", _stub_pdf)
    monkeypatch.setattr(audit_main, "duplication_report", lambda: {"available": False})
    _suite._write_state(tmp_path, {"running": True, "error": None, "pid": os.getpid()})

    _suite.run_coverage_and_rebuild(tmp_path)

    assert _suite.refresh_state(tmp_path) == {"running": False, "error": None}
    assert (tmp_path / "test_report.pdf").exists()
    assert (tmp_path / "audit_r3_test_coverage.pdf").exists()
    assert (tmp_path / "coding_rule_audit.pdf").exists()


def test_coverage_refresh_records_error(tmp_path, monkeypatch):
    def _boom(output_dir):
        raise RuntimeError("pytest exploded")

    monkeypatch.setattr(_suite, "run_test_suite", _boom)
    _suite._write_state(tmp_path, {"running": True, "error": None, "pid": os.getpid()})
    _suite.run_coverage_and_rebuild(tmp_path)
    state = _suite.refresh_state(tmp_path)
    assert state["running"] is False
    assert "pytest exploded" in state["error"]


def test_start_coverage_refresh_spawns_once_and_guards(tmp_path, monkeypatch):
    # Starts a background refresh when idle; refuses to stack a second one.
    spawned = []

    class _FakeThread:
        def __init__(self, target, args, daemon):
            self.args = args

        def start(self):
            spawned.append(self.args)

    monkeypatch.setattr(_suite.threading, "Thread", _FakeThread)
    monkeypatch.delenv(_suite.SUITE_ACTIVE_ENV, raising=False)     # not nested here

    assert _suite.start_coverage_refresh(tmp_path) is True
    assert _suite.refresh_state(tmp_path)["running"] is True and spawned == [(tmp_path,)]
    # Already running → no second thread.
    assert _suite.start_coverage_refresh(tmp_path) is False
    assert len(spawned) == 1


def test_start_coverage_refresh_declines_when_nested_in_a_suite(tmp_path, monkeypatch):
    # A generate fired from inside a running suite must not spawn another suite.
    monkeypatch.setenv(_suite.SUITE_ACTIVE_ENV, "1")
    assert _suite.start_coverage_refresh(tmp_path) is False
    assert _suite.refresh_state(tmp_path)["running"] is False    # never flipped on


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
    monkeypatch.setattr(_bp, "OUTPUT_DIR", out)

    catalogue = client.get("/api/audit-reports").get_json()
    by_name = {r["filename"]: r for r in catalogue}
    assert by_name["junit.xml"]["type"] == "XML"
    assert by_name["junit.xml"]["label"] == "JUnit Results"
    assert by_name["init_audit_results.json"]["type"] == "JSON"
    # The coverage HTML directory is surfaced as one card that opens its own page.
    by_label = {r["label"]: r for r in catalogue}
    cov = by_label[_bp.COVERAGE_HTML_LABEL]
    assert cov["type"] == "HTML" and cov["href"] == "coverage"


def test_catalogue_groups_artefacts_into_the_two_sub_tabs(client, tmp_path, monkeypatch):
    # The tab is split User / Code. The estate's own reports and the guides are the
    # user's; the rule reports and the test evidence are the code's — including the
    # report for a rule added later, since Code is what an unlisted artefact falls to.
    out = tmp_path / "audit"
    (out / "coverage").mkdir(parents=True)
    for name in ("model_risk_report.pdf", "completeness_audit.pdf", "user_guide.pdf",
                 "user_guide.docx", "integration_guide.pdf", "coding_rule_audit.pdf",
                 "audit_r1_hardcoded_parameters.pdf", "audit_r99_a_later_rule.pdf",
                 "junit.xml"):
        (out / name).write_bytes(b"stub")
    (out / "coverage" / "index.html").write_text("<html>cov</html>")
    monkeypatch.setattr(_bp, "OUTPUT_DIR", out)

    groups = {r["filename"]: r["group"]
              for r in client.get("/api/audit-reports").get_json()}
    assert {n for n, g in groups.items() if g == "user"} == {
        "model_risk_report.pdf", "completeness_audit.pdf", "user_guide.pdf",
        "user_guide.docx", "integration_guide.pdf"}
    assert groups["audit_r1_hardcoded_parameters.pdf"] == "code"
    assert groups["audit_r99_a_later_rule.pdf"] == "code"
    assert groups["coding_rule_audit.pdf"] == "code"
    assert groups["junit.xml"] == "code"
    assert groups["coverage/index.html"] == "code"


def test_serve_coverage_index_and_assets(client, tmp_path, monkeypatch):
    out = tmp_path / "audit"
    (out / "coverage").mkdir(parents=True)
    (out / "coverage" / "index.html").write_text("<html>cov index</html>")
    (out / "coverage" / "style.css").write_text("body{}")
    monkeypatch.setattr(_bp, "OUTPUT_DIR", out)

    assert b"cov index" in client.get("/api/audit-reports/coverage").data
    assert b"body{}" in client.get("/api/audit-reports/coverage/style.css").data


def test_serve_coverage_404_when_absent(client, tmp_path, monkeypatch):
    monkeypatch.setattr(_bp, "OUTPUT_DIR", tmp_path / "audit")
    assert client.get("/api/audit-reports/coverage").status_code == 404
    assert client.get("/api/audit-reports/coverage/style.css").status_code == 404


def test_serve_non_pdf_downloads_as_attachment(client, tmp_path, monkeypatch):
    out = tmp_path / "audit"
    out.mkdir()
    (out / "junit.xml").write_text("<testsuite/>")
    monkeypatch.setattr(_bp, "OUTPUT_DIR", out)
    res = client.get("/api/audit-reports/junit.xml")
    assert res.status_code == 200
    assert "attachment" in res.headers.get("Content-Disposition", "")


def test_serve_missing_dir_is_404(client, tmp_path, monkeypatch):
    monkeypatch.setattr(_bp, "OUTPUT_DIR", tmp_path / "audit")
    assert client.get("/api/audit-reports/anything.pdf").status_code == 404


def test_serve_unknown_file_is_404(client, tmp_path, monkeypatch):
    out = tmp_path / "audit"
    out.mkdir()
    monkeypatch.setattr(_bp, "OUTPUT_DIR", out)
    assert client.get("/api/audit-reports/nope.pdf").status_code == 404


# --- The refresh flag is shared, because the workers are not ------------------
# Under gunicorn, a flag in module state is per-process: the worker answering the
# status poll is usually not the one running the refresh, so the UI saw "finished"
# seconds in and showed the previous run's coverage as this run's output.


def test_the_refresh_state_is_read_from_disk_not_from_this_process(tmp_path):
    """A refresh started by ANOTHER process is still reported as running."""
    _suite._write_state(tmp_path, {"running": True, "error": None, "pid": 1})
    assert _suite.refresh_state(tmp_path)["running"] is True     # pid 1 is alive


def test_a_refresh_whose_process_died_is_reported_interrupted(tmp_path):
    """The killed-mid-run case: the artefacts never arrived, and saying nothing
    would present the previous run's coverage as this run's result."""
    dead = _dead_pid()
    _suite._write_state(tmp_path, {"running": True, "error": None, "pid": dead})
    state = _suite.refresh_state(tmp_path)
    assert state["running"] is False
    assert "stopped before it finished" in state["error"]


def test_a_missing_or_unreadable_state_file_reads_as_idle(tmp_path):
    """Never generated, or truncated by hand: neither may 500 the status endpoint."""
    idle = {"running": False, "error": None}
    assert _suite.refresh_state(tmp_path) == idle
    (tmp_path / _suite.REFRESH_STATE_NAME).write_text("{not json", encoding="utf-8")
    assert _suite.refresh_state(tmp_path) == idle


def test_the_write_lock_is_reentrant_across_sequential_holders(tmp_path):
    """Two passes in a row each acquire and release; neither deadlocks."""
    for _ in range(2):
        with _suite.write_lock(tmp_path):
            pass
    assert (tmp_path / _suite.REFRESH_WRITE_LOCK_NAME).exists()


def test_the_coordination_files_stay_out_of_the_catalogue(tmp_path, monkeypatch):
    """They are dotfiles precisely so the tab does not list them as artefacts."""
    monkeypatch.setattr(_bp, "OUTPUT_DIR", tmp_path)
    _suite._write_state(tmp_path, {"running": False, "error": None, "pid": 1})
    with _suite.write_lock(tmp_path):
        pass
    (tmp_path / "user_guide.pdf").write_bytes(b"%PDF-1.4")
    assert [row["filename"] for row in _bp.catalogue()] == ["user_guide.pdf"]


def _dead_pid() -> int:
    """A pid that is certainly not running: spawn a trivial child and reap it."""
    import subprocess
    proc = subprocess.Popen(["true"])
    proc.wait()
    return proc.pid
