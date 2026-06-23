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
"""Audit: duplicate-code detection (jscpd wrapper, report-only)."""
from __future__ import annotations

import audit.duplication as dup
from audit.duplication import _summarise, duplication_report, jscpd_available
from config.audit import DUPLICATION_MAX_PERCENT

_REPORT = {
    "statistics": {"total": {"percentage": 12.345, "clones": 2, "duplicatedLines": 40}},
    "duplicates": [
        {"firstFile": {"name": "a.py"}, "secondFile": {"name": "b.py"}, "lines": 10},
        {"firstFile": {"name": "c.py"}, "secondFile": {"name": "d.py"}, "lines": 20},
    ],
}


def test_summarise_rounds_and_sorts():
    summary = _summarise(_REPORT)
    assert summary["percentage"] == 12.35
    assert summary["clones"] == 2 and summary["duplicated_lines"] == 40
    assert summary["pairs"][0]["lines"] == 20  # largest clone first


def test_jscpd_available_returns_bool():
    assert isinstance(jscpd_available(), bool)


def test_report_when_jscpd_missing(monkeypatch):
    monkeypatch.setattr(dup.shutil, "which", lambda _name: None)
    assert duplication_report() == {"available": False}


def test_repo_duplication_below_threshold():
    report = duplication_report()
    if report.get("available"):
        assert report["percentage"] < DUPLICATION_MAX_PERCENT
