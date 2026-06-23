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
"""Duplicate-code audit: thin wrapper over jscpd (report-only)."""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from config.audit import JSCPD_MIN_LINES, JSCPD_MIN_TOKENS

from audit._walk import REPO_ROOT


def jscpd_available() -> bool:
    return shutil.which("jscpd") is not None


def _summarise(report: dict) -> dict:
    stats = report.get("statistics", {}).get("total", {})
    clones = report.get("duplicates", [])
    pairs = sorted(
        ({"first": c["firstFile"]["name"], "second": c["secondFile"]["name"],
          "lines": c.get("lines", 0)} for c in clones),
        key=lambda c: c["lines"], reverse=True)
    return {
        "percentage": round(float(stats.get("percentage", 0.0)), 2),
        "clones": int(stats.get("clones", 0)),
        "duplicated_lines": int(stats.get("duplicatedLines", 0)),
        "pairs": pairs[:20],
    }


def duplication_report(target: str = "src") -> dict:
    """Run jscpd over ``target`` and summarise; ``available`` False if jscpd absent."""
    if not jscpd_available():
        return {"available": False}
    with tempfile.TemporaryDirectory() as out:
        subprocess.run(
            ["jscpd", str(REPO_ROOT / target), "--format", "python,javascript",
             "--min-lines", str(JSCPD_MIN_LINES), "--min-tokens", str(JSCPD_MIN_TOKENS),
             "--reporters", "json", "--output", out, "--silent"],
            capture_output=True, check=False)
        report_path = Path(out) / "jscpd-report.json"
        if not report_path.exists():
            return {"available": True, "percentage": 0.0, "clones": 0,
                    "duplicated_lines": 0, "pairs": []}
        summary = _summarise(json.loads(report_path.read_text(encoding="utf-8")))
        summary["available"] = True
        return summary
