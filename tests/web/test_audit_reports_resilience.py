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
"""What the audit-report run does when one part of it fails.

The rule the whole endpoint is built around: a single report blowing up must not
leave every report after it silently keeping its previous file and previous date.
That is the "the reports are two days old" symptom, and it is worse than a named
failure because nobody sees it.
"""
from __future__ import annotations

import os

import pytest

from src.governance.mrc.pack import TectonicNotFound
from src.web.api_audit_reports import _guides, _suite
from src.web.api_audit_reports.generate import write_one


def test_a_failing_report_is_named_rather_than_swallowed(tmp_path):
    errors: list = []
    dest = tmp_path / "model_risk_report.pdf"

    def _blows_up():
        raise RuntimeError("tectonic hiccup")

    write_one(dest, _blows_up, errors)
    assert errors == [("model_risk_report.pdf", "tectonic hiccup")]
    assert not dest.exists(), "no partial file is left carrying today's date"


def test_a_missing_engine_stops_the_run_rather_than_being_recorded(tmp_path):
    """No engine means nothing can be produced, so recording it per report would
    return a list of identical failures instead of one actionable 503."""
    errors: list = []

    def _no_engine():
        raise TectonicNotFound("tectonic is not installed")

    with pytest.raises(TectonicNotFound):
        write_one(tmp_path / "model_risk_report.pdf", _no_engine, errors)
    assert errors == []


def test_a_report_that_renders_is_written(tmp_path):
    errors: list = []
    dest = tmp_path / "model_risk_report.pdf"
    write_one(dest, lambda: b"%PDF-1.4 stub", errors)
    assert dest.read_bytes() == b"%PDF-1.4 stub"
    assert errors == []


def test_the_editable_guide_is_skipped_when_pandoc_is_absent(tmp_path, monkeypatch):
    """Both forms come from the one markdown source; without pandoc the Word one
    simply is not published, rather than the run failing over an optional tool."""
    monkeypatch.setattr(_guides.shutil, "which", lambda _name: None)
    dest = tmp_path / "user_guide.docx"
    _guides.render_user_guide_docx(dest)
    assert not dest.exists()


def test_a_pid_that_cannot_be_asked_about_is_treated_as_gone(monkeypatch):
    """A refresh whose process cannot be probed must read as finished, or the
    lock it left behind would block every later run for good."""
    def _refuses(pid, sig):
        raise OSError("cannot signal that process")

    monkeypatch.setattr(os, "kill", _refuses)
    assert _suite._alive(1) is False
