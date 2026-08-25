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
"""The finding-history observation schedule.

Ageing a finding needs somebody to have looked before today, and the audit keeps no
memory of its own. This is the thing that looks.

**On a schedule, never on a request.** The console and the ERM API are both
documented as reads, and observing on a GET would make both claims false — as well
as writing at whatever rate the ERM happened to poll. Once a day, from one process.

**This must run in exactly one process**, for the same reason the backup schedule
must: under gunicorn it starts in the *master* before the fork, or every worker
would run a completeness scan simultaneously every day, and a worker gunicorn later
recycled would take the schedule down with it.

The thread is a daemon and every run is best-effort. A failed observation (database
down, a scan that raised) is logged and the schedule carries on: it costs a gap in
the series, and a missing day is a far smaller thing than an observer that took the
application down with it.
"""
from __future__ import annotations

import logging
import threading

from config.history import (HISTORY_ENABLED, HISTORY_INTERVAL_SECONDS,
                            HISTORY_STARTUP_DELAY_SECONDS)

logger = logging.getLogger(__name__)

THREAD_NAME = "finding-history"


def run_observation() -> bool:
    """Look once. Returns whether it succeeded; never raises."""
    try:
        from src.governance.attention import observe   # lazy: keeps import cheap
        result = observe()
        logger.info("finding history: %s", result)
        return True
    except Exception:  # noqa: BLE001 — an observation may never disturb the app
        logger.exception("finding-history observation did not run")
        return False


def history_loop(stop: threading.Event, interval: float, delay: float) -> int:
    """Observe after ``delay``, then every ``interval``, until ``stop`` is set.

    Returns how many observations were attempted. Waits on the event rather than
    sleeping, so a shutdown is acted on at once instead of after the rest of a day.
    """
    attempts = 0
    if stop.wait(delay):
        return attempts
    while True:
        run_observation()
        attempts += 1
        if stop.wait(interval):
            return attempts


def start(stop: threading.Event | None = None) -> threading.Thread | None:
    """Start the schedule in a daemon thread, or return ``None`` if disabled.

    ``stop`` is accepted so a caller (and the tests) can shut the loop down; the
    daemon flag means a process that simply exits is not held open by it.
    """
    if not HISTORY_ENABLED:
        logger.info("finding history disabled; the trend and finding ages stay empty")
        return None
    thread = threading.Thread(
        target=history_loop, name=THREAD_NAME, daemon=True,
        args=(stop or threading.Event(), HISTORY_INTERVAL_SECONDS,
              HISTORY_STARTUP_DELAY_SECONDS))
    thread.start()
    return thread
