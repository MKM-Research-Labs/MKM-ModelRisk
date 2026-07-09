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
