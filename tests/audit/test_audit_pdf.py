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
"""Tests for the coding-rule audit PDF builder."""
from __future__ import annotations

from audit.pdf import build_audit_tex, render_audit_pdf
from src.governance.mrc import pack

_CLEAN = {
    "large_source_files": [], "large_test_files": [], "hardcoding": [],
    "embedded_js": [], "init_files": [], "headers": [],
    "duplication": {"available": True, "percentage": 0.5, "clones": 3},
}
_FINDINGS = {
    "large_source_files": [{"path": "x.py", "lines": 350}],
    "large_test_files": [],
    "hardcoding": [{"path": "y.py", "line": 4, "kind": "allcaps", "name": "MAXN"}],
    "embedded_js": [{"path": "z.py", "line": 9, "kind": "script", "js_lines": 5}],
    "init_files": [{"path": "p.py", "functions": ["f"], "classes": ["C"]}],
    "headers": [{"path": "h.py"}],
    "duplication": {"available": False},
}


def test_build_audit_tex_clean():
    tex = build_audit_tex(_CLEAN, "2026-06-25")
    assert "Coding-Rule Audit Report" in tex
    assert "2026-06-25" in tex
    assert "No findings." in tex
    assert "0.5\\%" in tex
    assert tex.strip().endswith("\\end{document}")


def test_summary_table_lists_every_rule_in_order():
    tex = build_audit_tex(_CLEAN, "2026-06-25")
    # One row per rule, with a short requirement, in ascending order R1–R8.
    markers = ["config package", "size limit", "test coverage", "init",
               "copyright header", "src/database", "embedded in", "duplicated code"]
    positions = [tex.index(m) for m in markers]
    assert positions == sorted(positions)
    assert "by code review" in tex          # R6 result
    assert "Pass" in tex                     # mechanical-rule result


def test_build_audit_tex_with_findings():
    tex = build_audit_tex(_FINDINGS, "2026-06-25")
    assert "x.py" in tex and "350" in tex
    assert "y.py" in tex
    assert "z.py" in tex and "script" in tex
    assert "h.py" in tex                      # R5 missing-header finding
    assert "not measured" in tex


def test_render_audit_pdf(monkeypatch):
    monkeypatch.setattr(pack, "compile_tex", lambda tex, assets=None: b"%PDF-stub")
    assert render_audit_pdf(_CLEAN, "2026-06-25") == b"%PDF-stub"
