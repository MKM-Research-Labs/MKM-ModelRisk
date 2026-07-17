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
"""Audit (reported): a licence notice on every non-.py/.js file (coding rule R5)."""
from __future__ import annotations

from audit.notices import _in_scope, _is_marked, notice_findings

from config.audit import NOTICE_SIBLING_SUFFIX


def test_every_first_party_file_carries_a_notice():
    assert notice_findings() == []


def test_marked_by_an_inline_notice(tmp_path):
    f = tmp_path / "schema.sql"
    f.write_text("-- Copyright (c) 2022-2026 MKM Research Labs. "
                 "Licensed under the MIT License; see LICENSE.\nSELECT 1;\n")
    assert _is_marked(f)


def test_unmarked_when_the_notice_is_absent(tmp_path):
    f = tmp_path / "schema.sql"
    f.write_text("SELECT 1;\n")
    assert not _is_marked(f)


def test_a_sibling_license_file_marks_an_uncommentable_file(tmp_path):
    """JSON forbids comments, so the sibling carries the notice instead."""
    f = tmp_path / "data.json"
    f.write_text('{"a": 1}\n')
    assert not _is_marked(f)
    (tmp_path / ("data.json" + NOTICE_SIBLING_SUFFIX)).write_text("MIT License\n")
    assert _is_marked(f)


def test_binary_without_a_sibling_is_unmarked(tmp_path):
    f = tmp_path / "logo.png"
    f.write_bytes(b"\x89PNG\r\n\x1a\n\x00\xff\xfe")
    assert not _is_marked(f)


def test_py_and_js_are_out_of_scope_the_header_gate_owns_them(tmp_path):
    assert not _in_scope(tmp_path / "mod.py")
    assert not _in_scope(tmp_path / "ui.js")


def test_license_itself_and_sibling_markers_are_out_of_scope(tmp_path):
    assert not _in_scope(tmp_path / "LICENSE")
    assert not _in_scope(tmp_path / ("data.json" + NOTICE_SIBLING_SUFFIX))


def test_generated_and_local_files_are_out_of_scope(tmp_path):
    """.env holds secrets; the rest are build artefacts — never first-party."""
    for name in (".env", ".DS_Store", "coverage.xml", ".coverage"):
        assert not _in_scope(tmp_path / name)


def test_local_only_notes_are_out_of_scope(tmp_path):
    """*.local.md is gitignored internal planning (e.g. PROJECT_PLAN.local.md);
    it never ships, so the notice scan must not report it."""
    assert not _in_scope(tmp_path / "PROJECT_PLAN.local.md")
    # A committed .md is still in scope.
    assert _in_scope(tmp_path / "README.md")
