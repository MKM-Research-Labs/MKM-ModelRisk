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
"""The in-app database backup schedule.

In-app rather than a system scheduler: macOS blocks a background LaunchAgent
from reading the repo under ~/Documents, but the app inherits the launching
shell's permissions, so the backup script runs cleanly from here.

**This must run in exactly one process.** Under the development server that is
the app process itself. Under gunicorn it is the *master* — started from
``on_starting`` in ``gunicorn.conf.py``, before the fork — because starting it
per worker would mean a simultaneous dump per worker every hour, and because a
worker gunicorn later recycles would take the schedule down with it.

The thread is a daemon, so it dies with whichever process owns it, and every run
is best-effort: a failed or skipped dump (database down, volume unmounted) is
logged and the schedule carries on. A backup that broke the request loop would
be worse than one that is occasionally missed.
"""
from __future__ import annotations

import logging
import subprocess
import threading

from config.backup import (BACKUP_ENABLED, BACKUP_INTERVAL_SECONDS,
                           BACKUP_STARTUP_DELAY_SECONDS, BACKUP_TIMEOUT_SECONDS)
from config.paths import BACKUP_SCRIPT

logger = logging.getLogger(__name__)

THREAD_NAME = "db-backup"


def run_backup(timeout: float | None = None) -> bool:
    """Take one dump. Returns whether it succeeded; never raises."""
    limit = BACKUP_TIMEOUT_SECONDS if timeout is None else timeout
    try:
        completed = subprocess.run(
            ["bash", str(BACKUP_SCRIPT)], timeout=limit, check=False)
    except Exception:  # noqa: BLE001 — a backup may never disturb the app
        logger.exception("database backup did not run")
        return False
    if completed.returncode != 0:
        logger.warning("database backup exited %s", completed.returncode)
        return False
    return True


def backup_loop(stop: threading.Event, interval: float, delay: float) -> int:
    """Dump after ``delay``, then every ``interval``, until ``stop`` is set.

    Returns how many dumps were attempted. Waits on the event rather than
    sleeping so a shutdown is acted on at once instead of after the rest of an
    hour.
    """
    attempts = 0
    if stop.wait(delay):
        return attempts
    while True:
        run_backup()
        attempts += 1
        if stop.wait(interval):
            return attempts


def start_backup_scheduler(interval: float | None = None,
                           delay: float | None = None) -> threading.Event | None:
    """Start the backup thread; return the event that stops it.

    Returns ``None``, having started nothing, when backups are switched off —
    see ``BACKUP_ENABLED`` in config/backup.py for why the verification app does
    that.
    """
    if not BACKUP_ENABLED:
        logger.info("database backup schedule disabled via BACKUP_ENABLED")
        return None

    stop = threading.Event()
    threading.Thread(
        target=backup_loop,
        args=(stop,
              BACKUP_INTERVAL_SECONDS if interval is None else interval,
              BACKUP_STARTUP_DELAY_SECONDS if delay is None else delay),
        daemon=True, name=THREAD_NAME).start()
    logger.info("database backup scheduled every %ss", BACKUP_INTERVAL_SECONDS)
    return stop
