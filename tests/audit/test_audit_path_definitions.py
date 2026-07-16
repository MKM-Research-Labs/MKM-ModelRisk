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
"""Path-definition audit: filesystem paths belong in the config package."""
from __future__ import annotations

from audit.path_definitions import _scan_text, path_definition_findings


def test_flags_root_walk_and_data_paths():
    text = (
        "root = Path(__file__).resolve().parents[1]\n"
        "here = os.path.dirname(__file__)\n"
        "d = root / 'uploads'\n"
        "p = os.path.join(root, 'uploads')\n"
        "lit = 'uploads/audit'\n"
    )
    kinds = [f["kind"] for f in _scan_text(text, "m.py")]
    assert kinds == ["root_walk", "root_walk", "data_literal", "data_literal",
                     "data_literal"]


def test_ignores_comments_and_docstrings():
    text = (
        '"""Files live under uploads/ — Path(__file__).parents[1]."""\n'
        "# root = Path(__file__).parents[1]\n"
        "x = 1\n"
    )
    assert _scan_text(text, "m.py") == []


def test_incidental_substring_is_not_a_data_literal():
    # A URL that merely contains the tree name is not a path definition.
    text = "url = 'https://host/uploads/logo.png'\n"
    assert _scan_text(text, "m.py") == []


def test_findings_are_sorted_and_exclude_sanctioned_packages():
    findings = path_definition_findings()
    assert findings == sorted(findings, key=lambda f: (f["path"], f["line"]))
    for f in findings:
        assert {"path", "line", "kind", "snippet"} <= set(f)
        # config/ owns path definitions; the auditor bootstraps its own root.
        assert not f["path"].startswith(("config/", "audit/"))
