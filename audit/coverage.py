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
"""R3: test-coverage summary parsed from the Cobertura ``coverage.xml``.

The coverage gate itself is enforced by pyproject's ``fail_under`` when the
suite runs; this module parses the emitted ``coverage.xml`` so the audit report
can show the achieved line rate and surface any package that sits below the
minimum. It is reported (non-gating) — a missing ``coverage.xml`` yields an
empty summary (``available=False``) rather than an error, so the audit still
runs on a checkout that has not produced a coverage report.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from config.audit import COVERAGE_MINIMUM

from audit._walk import REPO_ROOT

# Default location of the Cobertura report, written by ``coverage xml`` or
# ``pytest --cov --cov-report=xml`` at the repo root.
COVERAGE_XML = REPO_ROOT / "coverage.xml"


def _package_rows(root: ET.Element) -> list[dict]:
    """Per-package line coverage, lowest rate first.

    ``coverage.py``'s Cobertura output puts totals only on the root; ``class``
    elements carry ``<line hits=…>`` children, so per-package valid/covered are
    counted from those (with a fast path for reports that do annotate the class
    totals directly).
    """
    rows: list[dict] = []
    for pkg in root.findall(".//package"):
        name = pkg.get("name", "").lstrip(".")
        if not name:
            continue
        rate = float(pkg.get("line-rate", 0))
        valid = sum(int(c.get("lines-valid", 0)) for c in pkg.findall("classes/class"))
        covered = sum(int(c.get("lines-covered", 0)) for c in pkg.findall("classes/class"))
        if valid == 0:
            lines = [ln for c in pkg.findall("classes/class") for ln in c.findall(".//line")]
            valid = len(lines)
            covered = sum(1 for ln in lines if ln.get("hits", "0") != "0")
        if valid > 0:
            rows.append({"package": name, "rate": rate * 100, "valid": valid,
                         "covered": covered, "gap": valid - covered})
    rows.sort(key=lambda r: r["rate"])
    return rows


def coverage_summary(cov_path: Path | None = None) -> dict:
    """Parse ``coverage.xml`` into an overall + per-package coverage summary.

    Returns ``{"available": False, ...}`` with zeroed totals when the report is
    absent, so callers can render a placeholder without special-casing.
    """
    path = COVERAGE_XML if cov_path is None else cov_path
    summary = {
        "available": False,
        "line_rate": 0.0,
        "lines_valid": 0,
        "lines_covered": 0,
        "by_package": [],
    }
    if not path.exists():
        return summary

    root = ET.parse(str(path)).getroot()
    summary["available"] = True
    summary["line_rate"] = float(root.get("line-rate", 0))
    summary["lines_valid"] = int(root.get("lines-valid", 0))
    summary["lines_covered"] = int(root.get("lines-covered", 0))
    summary["by_package"] = _package_rows(root)
    return summary


def low_coverage_packages(summary: dict, threshold: int = COVERAGE_MINIMUM) -> list[dict]:
    """Packages below ``threshold`` percent line coverage, lowest first.

    Packages at or above the threshold (including fully-covered ones) are
    omitted — the report only surfaces what needs attention.
    """
    return [r for r in summary["by_package"] if r["rate"] < threshold]
