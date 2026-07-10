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
"""Coverage audit: parse the Cobertura ``coverage.xml`` into a summary (R3)."""
from __future__ import annotations

from audit.coverage import coverage_summary, low_coverage_packages

_COBERTURA = """<?xml version="1.0" ?>
<coverage line-rate="0.8" lines-valid="10" lines-covered="8">
  <packages>
    <package name=".src.models" line-rate="0.5">
      <classes>
        <class filename="src/models/a.py">
          <lines>
            <line number="1" hits="1"/>
            <line number="2" hits="0"/>
          </lines>
        </class>
      </classes>
    </package>
    <package name="src.util" line-rate="1.0">
      <classes>
        <class filename="src/util/b.py">
          <lines>
            <line number="1" hits="3"/>
          </lines>
        </class>
      </classes>
    </package>
  </packages>
</coverage>
"""


def _write_xml(tmp_path, text):
    path = tmp_path / "coverage.xml"
    path.write_text(text, encoding="utf-8")
    return path


def test_missing_report_is_unavailable(tmp_path):
    summary = coverage_summary(tmp_path / "does_not_exist.xml")
    assert summary["available"] is False
    assert summary["by_package"] == []


def test_parses_overall_and_per_package(tmp_path):
    summary = coverage_summary(_write_xml(tmp_path, _COBERTURA))
    assert summary["available"] is True
    assert summary["line_rate"] == 0.8
    assert summary["lines_valid"] == 10
    assert summary["lines_covered"] == 8

    # Per-package rows are counted from <line> children, lowest coverage first,
    # and the leading dot in the package name is stripped.
    pkgs = summary["by_package"]
    assert [p["package"] for p in pkgs] == ["src.models", "src.util"]
    assert pkgs[0] == {"package": "src.models", "rate": 50.0, "valid": 2,
                       "covered": 1, "gap": 1}
    assert pkgs[1]["rate"] == 100.0 and pkgs[1]["gap"] == 0


def test_low_coverage_packages_omits_those_at_or_above_threshold(tmp_path):
    summary = coverage_summary(_write_xml(tmp_path, _COBERTURA))
    low = low_coverage_packages(summary, threshold=99)
    assert [p["package"] for p in low] == ["src.models"]
    # A lenient threshold keeps everything below it.
    assert low_coverage_packages(summary, threshold=40) == []
