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
"""Audit gate: the canonical copyright header on every file (coding rule R5)."""
from __future__ import annotations

from audit.headers import _CANONICAL, _expected, _has_header, header_findings


def test_repo_has_no_missing_headers():
    assert header_findings() == []


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
