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

**Both the flag and the lock live on disk, not in module state.** The console runs
under gunicorn with several workers, and each holds its own copy of any module
global. A flag in memory means the worker answering ``/coverage-status`` is usually
not the worker running the refresh, so the poll reports "finished" within seconds
while the suite runs on for another twenty minutes -- and the tab then presents
coverage from the *previous* run as the output of this one. A ``threading.Lock``
has the matching hole: it serialises threads inside one worker while a second
worker renders into the same directory regardless, which is the clash the lock was
added to prevent. A state file and an ``flock`` are shared by every worker.
"""
from __future__ import annotations

import json
import os
import threading
from contextlib import contextmanager
from datetime import date
from pathlib import Path

from audit.__main__ import build_report, write_audit_reports
from audit.coverage import coverage_summary
from audit.pdf import render_test_report_pdf
from audit.testsuite import SUITE_ACTIVE_ENV, run_test_suite
from config.audit import (COVERAGE_XML_NAME, REFRESH_INTERRUPTED,
                          REFRESH_STATE_NAME, REFRESH_WRITE_LOCK_NAME,
                          TEST_REPORT_PDF_NAME)

try:                                             # POSIX only; absent on Windows
    import fcntl
except ImportError:                              # pragma: no cover - platform
    fcntl = None

# Guards this process's own threads. The file locks below carry the cross-worker
# half; this one keeps a single worker's threads off each other cheaply, and is the
# whole story on a platform without ``fcntl`` (where the server is single-process).
_thread_lock = threading.Lock()


def _alive(pid: int) -> bool:
    """Is ``pid`` still running? Signal 0 asks without delivering anything."""
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:                      # exists, owned by someone else
        return True
    except OSError:
        return False
    return True


@contextmanager
def _flock(path: Path):
    """Hold an exclusive lock on ``path`` for the block, across processes."""
    if fcntl is None:                            # pragma: no cover - platform
        yield
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


@contextmanager
def write_lock(output_dir):
    """Serialise every tectonic pass over ``output_dir``, across all workers.

    The synchronous generate() pass and the background rebuild render the same
    PDFs into the same directory; two overlapping passes can make a compile fail
    intermittently. Held only around the write, never around the ~1-min suite run.
    """
    with _thread_lock, _flock(Path(output_dir) / REFRESH_WRITE_LOCK_NAME):
        yield


def _state_path(output_dir) -> Path:
    return Path(output_dir) / REFRESH_STATE_NAME


def _write_state(output_dir, state: dict) -> None:
    """Replace the state file atomically, so no reader sees a half-written one."""
    path = _state_path(output_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(state), encoding="utf-8")
    tmp.replace(path)


def refresh_state(output_dir) -> dict:
    """``{running, error}`` for the refresh, as every worker sees it.

    A run whose owning process has gone reports ``running: False`` with
    ``REFRESH_INTERRUPTED``: the artefacts it was going to write never arrived, and
    saying nothing would leave the tab showing the previous run's coverage as this
    run's result.
    """
    try:
        state = json.loads(_state_path(output_dir).read_text(encoding="utf-8"))
    except (OSError, ValueError):                # never generated, or unreadable
        return {"running": False, "error": None}
    if not state.get("running"):
        return {"running": False, "error": state.get("error")}
    pid = state.get("pid")
    if pid and not _alive(pid):
        return {"running": False, "error": REFRESH_INTERRUPTED}
    return {"running": True, "error": None}


def run_coverage_and_rebuild(output_dir) -> None:
    """Run the suites into ``output_dir``, then rebuild the coverage-aware output.

    Emits ``coverage.xml``/``coverage/`` HTML/``junit.xml`` (+ best-effort
    ``e2e_junit.xml``), writes the Test Report from the parsed results, and
    re-renders the reports so R3 and the consolidated overview show live numbers.
    """
    try:
        results = run_test_suite(output_dir)
        as_of = date.today().isoformat()
        cov = coverage_summary(output_dir / COVERAGE_XML_NAME)
        # Serialise the rebuild against any synchronous generate() write so the
        # two tectonic passes never run on the same dir at once.
        with write_lock(output_dir):
            (output_dir / TEST_REPORT_PDF_NAME).write_bytes(
                render_test_report_pdf(results, cov, as_of))
            write_audit_reports(build_report(), as_of, output_dir)
        error = None
    except Exception as exc:                    # missing pytest, timeout, tectonic…
        error = str(exc)
    _write_state(output_dir, {"running": False, "error": error, "pid": os.getpid()})


def start_coverage_refresh(output_dir) -> bool:
    """Kick off a background suite/coverage refresh unless one is already running.

    Refuses to start when already inside a suite run (``SUITE_ACTIVE_ENV`` set) —
    e.g. an e2e test that POSTs to /generate while the e2e suite itself runs under
    an audit run — so a suite never recursively spawns another suite.
    """
    if os.environ.get(SUITE_ACTIVE_ENV):
        return False
    # Claim under the state file's own lock, so two workers handling two clicks at
    # once cannot both decide they are the one to start the suite.
    with _flock(_state_path(output_dir).with_suffix(".lock")):
        if refresh_state(output_dir)["running"]:
            return False
        _write_state(output_dir, {"running": True, "error": None, "pid": os.getpid()})
    threading.Thread(target=run_coverage_and_rebuild, args=(output_dir,),
                     daemon=True).start()
    return True
