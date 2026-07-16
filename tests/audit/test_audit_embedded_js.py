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
"""Audit gate: JavaScript/CSS embedded in .py files (coding rule R5)."""
from __future__ import annotations

from audit.embedded_js import (
    _SCRIPT_BLOCK,
    _js_line_count,
    _scan_blocks,
    _scan_factories,
    embedded_js_findings,
)

_SCRIPT = "<script>\nvar a = 1;\ndocument.getElementById('x');\nwindow.foo = 2;\n</script>"
_FACTORY = "\n".join([
    "var x = 1;", "const y = 2;", "let z = 3;", "document.body.append(x);",
    "window.foo();", "el.addEventListener('c', f);", "node.querySelector('.a');",
    "root.innerHTML = y;",
])


def test_js_line_count():
    assert _js_line_count("var a=1;\nplain prose here\nconst b=2;") == 2


def test_scan_blocks_flags_inline_script():
    found = _scan_blocks(_SCRIPT, _SCRIPT_BLOCK, "script", "v.py")
    assert found and found[0]["kind"] == "script" and found[0]["js_lines"] >= 3


def test_scan_blocks_ignores_external_src_script():
    assert _scan_blocks('<script src="/static/x.js"></script>', _SCRIPT_BLOCK, "script", "v.py") == []


def test_scan_factories_flags_js_built_in_python():
    found = _scan_factories(_FACTORY, "v.py")
    assert found and found[0]["js_lines"] >= 8


def test_scan_factories_ignores_short_runs():
    assert _scan_factories("var x = 1;\nconst y = 2;", "v.py") == []


def test_repo_has_no_embedded_js():
    assert embedded_js_findings() == []
