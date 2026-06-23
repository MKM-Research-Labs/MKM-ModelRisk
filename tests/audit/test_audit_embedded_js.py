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
