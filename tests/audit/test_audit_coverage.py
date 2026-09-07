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
"""Coverage audit: parse the Cobertura ``coverage.xml`` into a summary (R3)."""
from __future__ import annotations

import os

import audit.coverage as cov_mod
from audit.coverage import coverage_summary, default_coverage_path, low_coverage_packages

_COBERTURA = """<?xml version="1.0" ?>
<coverage line-rate="0.8" lines-valid="10" lines-covered="8">
  <packages>
    <package name=".src.models" line-rate="0.5">
      <classes>
        <class filename="src/models/a.py">
          <lines>
            <line number="1" hits="1"/>
            <line number="2" hits="0"/>
          </lines>
        </class>
      </classes>
    </package>
    <package name="src.util" line-rate="1.0">
      <classes>
        <class filename="src/util/b.py">
          <lines>
            <line number="1" hits="3"/>
          </lines>
        </class>
      </classes>
    </package>
  </packages>
</coverage>
"""


def _write_xml(tmp_path, text):
    path = tmp_path / "coverage.xml"
    path.write_text(text, encoding="utf-8")
    return path


def _at(path, when):
    """Write a report and stamp it, so "which is newer" is the test's to decide."""
    path.write_text("<coverage/>")
    os.utime(path, (when, when))
    return path


def test_the_newer_report_wins_whichever_place_it_is_in(tmp_path, monkeypatch):
    """The audit-dir copy used to be preferred unconditionally, which is silent
    staleness: a developer running ``coverage xml`` at the repo root got a fresh
    report and an R3 line quoting the audit tab's last refresh. On 2026-09-07 that
    line was three days and a whole module out of date, and nothing said so."""
    audit_copy = _at(tmp_path / "audit_coverage.xml", 1_000_000)
    root_copy = _at(tmp_path / "root_coverage.xml", 2_000_000)      # newer
    monkeypatch.setattr(cov_mod, "_AUDIT_COVERAGE_XML", audit_copy)
    monkeypatch.setattr(cov_mod, "COVERAGE_XML", root_copy)
    assert default_coverage_path() == root_copy


def test_the_audit_dir_copy_wins_when_it_is_the_newer_one(tmp_path, monkeypatch):
    """The other direction: refreshing from the Audit Reports tab must not be
    overruled by a root file left behind by an older run."""
    audit_copy = _at(tmp_path / "audit_coverage.xml", 2_000_000)    # newer
    root_copy = _at(tmp_path / "root_coverage.xml", 1_000_000)
    monkeypatch.setattr(cov_mod, "_AUDIT_COVERAGE_XML", audit_copy)
    monkeypatch.setattr(cov_mod, "COVERAGE_XML", root_copy)
    assert default_coverage_path() == audit_copy


def test_default_coverage_path_falls_back_to_repo_root(tmp_path, monkeypatch):
    # No audit-dir copy → the repo-root location is used (legacy pytest --cov).
    monkeypatch.setattr(cov_mod, "_AUDIT_COVERAGE_XML", tmp_path / "absent.xml")
    assert default_coverage_path() == cov_mod.COVERAGE_XML


def test_with_neither_present_the_root_path_is_named(tmp_path, monkeypatch):
    """Something has to be returned for the "no report" branch to report on."""
    monkeypatch.setattr(cov_mod, "_AUDIT_COVERAGE_XML", tmp_path / "absent-a.xml")
    monkeypatch.setattr(cov_mod, "COVERAGE_XML", tmp_path / "absent-b.xml")
    assert default_coverage_path() == tmp_path / "absent-b.xml"


def test_missing_report_is_unavailable(tmp_path):
    summary = coverage_summary(tmp_path / "does_not_exist.xml")
    assert summary["available"] is False
    assert summary["by_package"] == []


def test_parses_overall_and_per_package(tmp_path):
    summary = coverage_summary(_write_xml(tmp_path, _COBERTURA))
    assert summary["available"] is True
    assert summary["line_rate"] == 0.8
    assert summary["lines_valid"] == 10
    assert summary["lines_covered"] == 8

    # Per-package rows are counted from <line> children, lowest coverage first,
    # and the leading dot in the package name is stripped.
    pkgs = summary["by_package"]
    assert [p["package"] for p in pkgs] == ["src.models", "src.util"]
    assert pkgs[0] == {"package": "src.models", "rate": 50.0, "valid": 2,
                       "covered": 1, "gap": 1}
    assert pkgs[1]["rate"] == 100.0 and pkgs[1]["gap"] == 0


def test_low_coverage_packages_omits_those_at_or_above_threshold(tmp_path):
    summary = coverage_summary(_write_xml(tmp_path, _COBERTURA))
    low = low_coverage_packages(summary, threshold=99)
    assert [p["package"] for p in low] == ["src.models"]
    # A lenient threshold keeps everything below it.
    assert low_coverage_packages(summary, threshold=40) == []
