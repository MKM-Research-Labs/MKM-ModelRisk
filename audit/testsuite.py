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
"""Run the test suites and emit their evidence artefacts into the audit output dir.

Mirrors PhysicalRisk: the audit run itself executes pytest with coverage + JUnit,
dropping ``coverage.xml``, the browsable ``coverage/`` HTML tree and ``junit.xml``
next to the report PDFs, plus a best-effort ``e2e_junit.xml`` from the Playwright
suite. Each JUnit report is parsed back into pass/fail counts so the Test Report
PDF can summarise the run. The suite is always pinned to the dedicated
``mkm_modelrisk_test`` database so a live or demo event store is never touched.
"""
from __future__ import annotations

import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from config.audit import (COVERAGE_HTML_DIRNAME, COVERAGE_XML_NAME,
                          E2E_JUNIT_XML_NAME, JUNIT_XML_NAME,
                          SUITE_TIMEOUT_SECONDS)

from audit._walk import REPO_ROOT

_TEST_DB = "mkm_modelrisk_test"

# Set on every suite subprocess so a nested audit run — e.g. an e2e test that
# POSTs to /generate while the e2e suite is itself running under an audit run —
# can detect it is inside a suite and refuse to spawn another one (recursion).
SUITE_ACTIVE_ENV = "AUDIT_SUITE_ACTIVE"


def _unit_cmd(output_dir: Path, python_exe: str) -> list[str]:
    """pytest for the unit/model suite with coverage (xml + html) and JUnit."""
    return [python_exe, "-m", "pytest", "-m", "not e2e",
            "--cov", f"--cov-report=xml:{output_dir / COVERAGE_XML_NAME}",
            f"--cov-report=html:{output_dir / COVERAGE_HTML_DIRNAME}",
            f"--junitxml={output_dir / JUNIT_XML_NAME}", "-q"]


def _e2e_cmd(output_dir: Path, python_exe: str) -> list[str]:
    """pytest for the Playwright e2e suite, emitting its own JUnit report."""
    return [python_exe, "-m", "pytest", "tests/e2e", "-m", "e2e",
            f"--junitxml={output_dir / E2E_JUNIT_XML_NAME}", "-q"]


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    """Run a pytest command from the repo root, pinned to the test database."""
    env = {**os.environ, "PYTHONUNBUFFERED": "1", "DB_NAME": _TEST_DB,
           SUITE_ACTIVE_ENV: "1"}
    return subprocess.run(cmd, cwd=str(REPO_ROOT), env=env,
                          capture_output=True, timeout=SUITE_TIMEOUT_SECONDS, check=False)


def parse_junit(path: Path) -> dict | None:
    """Parse a JUnit XML report into aggregate counts, or ``None`` if absent.

    Handles both a ``<testsuites>`` wrapper and a bare ``<testsuite>`` root.
    """
    path = Path(path)
    if not path.exists():
        return None
    root = ET.parse(str(path)).getroot()
    suites = root.findall("testsuite") if root.tag == "testsuites" else [root]
    tally = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0, "time": 0.0}
    for suite in suites:
        for key in ("tests", "failures", "errors", "skipped"):
            tally[key] += int(suite.get(key, 0))
        tally["time"] += float(suite.get("time", 0) or 0)
    tally["passed"] = tally["tests"] - tally["failures"] - tally["errors"] - tally["skipped"]
    return tally


def run_test_suite(output_dir, python_exe: str | None = None,
                   include_e2e: bool = True) -> dict:
    """Run the suites into ``output_dir``; return parsed ``{unit, e2e}`` counts.

    The unit suite always runs. The e2e suite is best-effort — a missing
    Playwright install, an unavailable browser or a boot failure leaves
    ``e2e=None`` (and no ``e2e_junit.xml``) rather than failing the whole run.
    """
    python_exe = python_exe or sys.executable
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    _run(_unit_cmd(output_dir, python_exe))
    unit = parse_junit(output_dir / JUNIT_XML_NAME)

    e2e = None
    if include_e2e:
        try:
            _run(_e2e_cmd(output_dir, python_exe))
            e2e = parse_junit(output_dir / E2E_JUNIT_XML_NAME)
        except (subprocess.SubprocessError, OSError):
            e2e = None
    return {"unit": unit, "e2e": e2e}
