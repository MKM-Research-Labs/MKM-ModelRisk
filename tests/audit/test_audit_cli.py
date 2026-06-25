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
"""Audit CLI: the consolidated ``python -m audit`` report."""
from __future__ import annotations

import audit.__main__ as cli
from audit.__main__ import build_report, main

_SECTIONS = {
    "large_source_files", "large_test_files", "hardcoding",
    "embedded_js", "init_files", "headers", "duplication",
}


def test_build_report_has_every_section(monkeypatch):
    monkeypatch.setattr(cli, "duplication_report", lambda: {"available": False})
    assert set(build_report()) == _SECTIONS


def test_main_prints_report_and_returns_code(monkeypatch, capsys):
    monkeypatch.setattr(cli, "duplication_report", lambda: {"available": False})
    code = main()
    out = capsys.readouterr().out
    assert "coding-rule audit" in out
    assert "Coverage gate" in out
    assert "jscpd not installed" in out
    assert code in (0, 1)
