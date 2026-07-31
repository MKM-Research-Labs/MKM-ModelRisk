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
"""The background test-suite refresh, and the lock that serialises writers.

Generate returns as soon as the reports are written and leaves the ~1-minute suite
run to a thread, which then re-renders the coverage-dependent reports. Both writers
render PDFs with tectonic into the same directory, so both take ``write_lock``
first: two overlapping passes are the likely cause of the intermittent compile
failure that used to leave half the tab stale.
"""
from __future__ import annotations

import os
import threading
from datetime import date

from audit.__main__ import build_report, write_audit_reports
from audit.coverage import coverage_summary
from audit.pdf import render_test_report_pdf
from audit.testsuite import SUITE_ACTIVE_ENV, run_test_suite
from config.audit import COVERAGE_XML_NAME, TEST_REPORT_PDF_NAME

# Background full-suite refresh. The suite takes ~1 min, so generation returns
# immediately and refreshes the coverage/JUnit artefacts, the Test Report and the
# coverage-dependent reports (R3 + the consolidated overview) once it lands.
cov_lock = threading.Lock()
cov_state = {"running": False, "error": None}

# Serialises every writer of the output dir — the synchronous generate() pass and
# the background coverage rebuild both render the same PDFs with tectonic, and two
# such passes overlapping (a second click, or a click landing on the tail of the
# previous refresh) can make a compile fail intermittently. Held only around the
# write, never around the ~1-min suite run.
write_lock = threading.Lock()


def run_coverage_and_rebuild(output_dir) -> None:
    """Run the suites into ``output_dir``, then rebuild the coverage-aware output.

    Emits ``coverage.xml``/``coverage/`` HTML/``junit.xml`` (+ best-effort
    ``e2e_junit.xml``), writes the Test Report from the parsed results, and
    re-renders the reports so R3 and the consolidated overview show live numbers.
    """
    global cov_state
    try:
        results = run_test_suite(output_dir)
        as_of = date.today().isoformat()
        cov = coverage_summary(output_dir / COVERAGE_XML_NAME)
        # Serialise the rebuild against any synchronous generate() write so the
        # two tectonic passes never run on the same dir at once.
        with write_lock:
            (output_dir / TEST_REPORT_PDF_NAME).write_bytes(
                render_test_report_pdf(results, cov, as_of))
            write_audit_reports(build_report(), as_of, output_dir)
        error = None
    except Exception as exc:                    # missing pytest, timeout, tectonic…
        error = str(exc)
    with cov_lock:
        cov_state["running"] = False
        cov_state["error"] = error


def start_coverage_refresh(output_dir) -> bool:
    """Kick off a background suite/coverage refresh unless one is already running.

    Refuses to start when already inside a suite run (``SUITE_ACTIVE_ENV`` set) —
    e.g. an e2e test that POSTs to /generate while the e2e suite itself runs under
    an audit run — so a suite never recursively spawns another suite.
    """
    if os.environ.get(SUITE_ACTIVE_ENV):
        return False
    with cov_lock:
        if cov_state["running"]:
            return False
        cov_state["running"] = True
        cov_state["error"] = None
    threading.Thread(target=run_coverage_and_rebuild, args=(output_dir,),
                     daemon=True).start()
    return True
