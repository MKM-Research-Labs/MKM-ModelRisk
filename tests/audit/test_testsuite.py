# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Test-suite runner: emits coverage/JUnit artefacts and parses their counts."""
from __future__ import annotations

import subprocess

import audit.testsuite as ts


def test_unit_cmd_wires_coverage_html_xml_and_junit(tmp_path):
    cmd = ts._unit_cmd(tmp_path, "py")
    joined = " ".join(cmd)
    assert "-m" in cmd and "not e2e" in cmd
    assert f"--cov-report=xml:{tmp_path / 'coverage.xml'}" in joined
    assert f"--cov-report=html:{tmp_path / 'coverage'}" in joined
    assert f"--junitxml={tmp_path / 'junit.xml'}" in joined


def test_e2e_cmd_targets_e2e_suite(tmp_path):
    cmd = ts._e2e_cmd(tmp_path, "py")
    assert "tests/e2e" in cmd and "e2e" in cmd
    assert f"--junitxml={tmp_path / 'e2e_junit.xml'}" in " ".join(cmd)


def test_run_pins_the_test_database_and_repo_root(monkeypatch):
    captured = {}

    def _fake_run(cmd, **kw):
        captured.update(cmd=cmd, env=kw.get("env"), cwd=kw.get("cwd"))
        return "done"

    monkeypatch.setattr(ts.subprocess, "run", _fake_run)
    assert ts._run(["pytest"]) == "done"
    assert captured["env"]["MKM_DB_NAME"] == "mkm_modelrisk_test"
    assert captured["env"][ts.SUITE_ACTIVE_ENV] == "1"        # marks nested runs
    assert captured["cwd"] == str(ts.REPO_ROOT)


_TESTSUITES = """<testsuites><testsuite tests="5" failures="1" errors="0" skipped="1" time="2.5"/>
<testsuite tests="3" failures="0" errors="1" skipped="0" time="1.0"/></testsuites>"""
_BARE = '<testsuite tests="4" failures="0" errors="0" skipped="2" time="0.4"/>'


def test_parse_junit_aggregates_testsuites_wrapper(tmp_path):
    p = tmp_path / "junit.xml"
    p.write_text(_TESTSUITES)
    r = ts.parse_junit(p)
    assert r["tests"] == 8 and r["failures"] == 1 and r["errors"] == 1
    assert r["skipped"] == 1 and r["passed"] == 5 and r["time"] == 3.5


def test_parse_junit_handles_bare_testsuite(tmp_path):
    p = tmp_path / "junit.xml"
    p.write_text(_BARE)
    r = ts.parse_junit(p)
    assert r["tests"] == 4 and r["skipped"] == 2 and r["passed"] == 2


def test_parse_junit_missing_file_is_none(tmp_path):
    assert ts.parse_junit(tmp_path / "absent.xml") is None


def test_run_test_suite_runs_unit_and_e2e(tmp_path, monkeypatch):
    def _fake_run(cmd):
        # Emulate pytest writing the JUnit report the command asked for.
        target = next(a.split("=", 1)[1] for a in cmd if a.startswith("--junitxml="))
        # ``--junitxml=path`` for unit; e2e passes it too.
        open(target, "w").write(_BARE)

    monkeypatch.setattr(ts, "_run", _fake_run)
    results = ts.run_test_suite(tmp_path, python_exe="py")
    assert results["unit"]["tests"] == 4 and results["e2e"]["tests"] == 4
    assert (tmp_path / "junit.xml").exists()


def test_run_test_suite_skips_e2e_when_disabled(tmp_path, monkeypatch):
    monkeypatch.setattr(ts, "_run",
                        lambda cmd: open(tmp_path / "junit.xml", "w").write(_BARE))
    results = ts.run_test_suite(tmp_path, python_exe="py", include_e2e=False)
    assert results["unit"]["tests"] == 4 and results["e2e"] is None


def test_run_test_suite_e2e_failure_is_best_effort(tmp_path, monkeypatch):
    calls = {"n": 0}

    def _fake_run(cmd):
        calls["n"] += 1
        if calls["n"] == 1:                       # unit run writes its report
            open(tmp_path / "junit.xml", "w").write(_BARE)
        else:                                     # e2e run blows up
            raise subprocess.SubprocessError("no browser")

    monkeypatch.setattr(ts, "_run", _fake_run)
    results = ts.run_test_suite(tmp_path, python_exe="py")
    assert results["unit"]["tests"] == 4 and results["e2e"] is None
