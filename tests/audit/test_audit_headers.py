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
"""Audit gate: the canonical copyright header on every file (coding rule R5)."""
from __future__ import annotations

from audit._walk import REPO_ROOT, rel
from audit.headers import (_CANONICAL, _expected, _has_header, _scan,
                           _strip_header, apply_headers, header_findings)


def test_repo_has_no_missing_headers():
    assert header_findings() == []


def test_canonical_block_matches_the_license_file():
    """The per-file header and LICENSE must state the same terms."""
    body = [line[2:] if line.startswith("# ") else line[1:] for line in _CANONICAL]
    licence = (REPO_ROOT / "LICENSE").read_text(encoding="utf-8").splitlines()
    # LICENSE opens with a title line and a blank; the rest is the header body.
    assert body[1:] == licence[3:]


def test_scope_covers_the_entry_point_and_the_tests():
    """R5 reads 'every first-party file' — not just the source dirs."""
    scanned = {rel(path) for path, _ in _scan()}
    assert "app.py" in scanned
    assert "tests/audit/test_audit_headers.py" in scanned


def test_apply_headers_is_a_noop_on_a_compliant_repo():
    assert apply_headers() == []


def test_strip_header_leaves_a_non_licence_comment_alone():
    lines = ["# -*- coding: utf-8 -*-", "import os"]
    assert _strip_header(lines, "#") == lines


def test_has_header_allows_a_shebang_above_it(tmp_path):
    f = tmp_path / "script.py"
    f.write_text("#!/usr/bin/env python3\n" + "\n".join(_CANONICAL) + "\n")
    assert _has_header(f, ".py")


def test_expected_js_variant_uses_double_slash():
    js = _expected(".js")
    assert js[0].startswith("// Copyright")
    assert all(not line.startswith("#") for line in js)


def test_has_header_true_for_canonical(tmp_path):
    f = tmp_path / "ok.py"
    f.write_text("\n".join(_CANONICAL) + "\n\nprint('hi')\n")
    assert _has_header(f, ".py")


def test_has_header_false_when_missing(tmp_path):
    f = tmp_path / "bad.py"
    f.write_text("print('no header')\n")
    assert not _has_header(f, ".py")
