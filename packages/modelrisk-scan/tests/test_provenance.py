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
"""Tests for provenance construction and git-commit discovery."""
from __future__ import annotations

import subprocess

from modelrisk_scan import build_provenance
from modelrisk_scan import provenance as prov_mod


def test_build_provenance_with_explicit_fields():
    prov = build_provenance(
        source_repo="PhysicalRisk", producer="modelrisk-scan/data-lineage",
        producer_version="0.1.0", commit="deadbeef",
        generated_at="2026-07-15T00:00:00Z",
    )
    assert prov == {
        "source_repo": "PhysicalRisk", "commit": "deadbeef",
        "producer": "modelrisk-scan/data-lineage", "producer_version": "0.1.0",
        "generated_at": "2026-07-15T00:00:00Z",
    }


def test_build_provenance_defaults_commit_and_timestamp(monkeypatch):
    monkeypatch.setattr(prov_mod, "_git_commit", lambda cwd=None: "cafebabe")
    prov = build_provenance(
        source_repo="R", producer="p", producer_version="1",
    )
    assert prov["commit"] == "cafebabe"
    assert prov["generated_at"].endswith("Z")  # RFC 3339 UTC


def test_build_provenance_unknown_commit_when_git_absent(monkeypatch):
    monkeypatch.setattr(prov_mod, "_git_commit", lambda cwd=None: None)
    prov = build_provenance(source_repo="R", producer="p", producer_version="1")
    assert prov["commit"] == "unknown"


def test_git_commit_reads_head_via_runner():
    def _fake_runner(cmd, cwd, capture_output, text, check):
        assert cmd == ["git", "rev-parse", "HEAD"]
        return subprocess.CompletedProcess(cmd, 0, stdout="abc123\n", stderr="")
    assert prov_mod._git_commit(runner=_fake_runner) == "abc123"


def test_git_commit_returns_none_on_failure():
    def _boom(*a, **k):
        raise subprocess.CalledProcessError(1, "git")
    assert prov_mod._git_commit(runner=_boom) is None
