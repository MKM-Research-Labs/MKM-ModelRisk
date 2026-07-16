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
"""JSON-file audit (coding rule R6): source persists via Postgres, not .json."""
from __future__ import annotations

from audit.json_files import _scan_text, json_file_findings


def test_flags_load_dump_and_path_literal():
    text = (
        "data = json.load(fh)\n"
        "json.dump(obj, fh)\n"
        'path = Path(base) / "models.json"\n'
    )
    findings = _scan_text(text, "m.py")
    assert [f["kind"] for f in findings] == ["load", "dump", "path"]
    assert [f["line"] for f in findings] == [1, 2, 3]


def test_bare_json_literal_without_fs_context_is_not_flagged():
    # A filename constant or a lookup-table value is not filesystem I/O.
    text = (
        'INIT_JSON = "init_audit_results.json"\n'
        'LABELS = {".json": "JSON"}\n'
    )
    assert _scan_text(text, "m.py") == []


def test_load_wins_over_path_on_same_line():
    # A line that both calls json.load and names a .json literal is one finding.
    findings = _scan_text('cfg = json.load(open("a.json"))\n', "m.py")
    assert len(findings) == 1 and findings[0]["kind"] == "load"


def test_ignores_comments_docstrings_and_allowlisted():
    text = (
        '"""Loads models.json via json.load()."""\n'
        "# json.dump(x, open('cache.json','w'))\n"
        'deps = json.load(open("package.json"))\n'   # allowlisted config artefact
        "x = 1\n"
    )
    assert _scan_text(text, "m.py") == []


def test_loads_string_helper_is_not_flagged():
    # json.loads/json.dumps operate on strings, not files — not file I/O.
    assert _scan_text("obj = json.loads(s)\nout = json.dumps(obj)\n", "m.py") == []


def test_findings_are_sorted_and_skip_auditor():
    findings = json_file_findings()
    assert findings == sorted(findings, key=lambda f: (f["path"], f["line"]))
    for f in findings:
        assert {"path", "line", "kind", "snippet"} <= set(f)
        assert not f["path"].startswith("audit/")
