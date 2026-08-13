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
"""The in-app backup schedule.

The behaviour that matters is that a failing dump is absorbed rather than
propagated — the schedule exists to protect the estate, and must never be the
thing that takes the console down.
"""
from __future__ import annotations

import subprocess
import threading

from src.web import _backup


class _Completed:
    def __init__(self, returncode):
        self.returncode = returncode


def test_run_backup_reports_success(monkeypatch):
    seen = {}

    def fake_run(cmd, timeout, check):
        seen["cmd"], seen["timeout"] = cmd, timeout
        return _Completed(0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert _backup.run_backup(timeout=7) is True
    assert seen["cmd"][0] == "bash"
    assert seen["cmd"][1].endswith("backup_db.sh")
    assert seen["timeout"] == 7


def test_run_backup_reports_a_non_zero_exit_without_raising(monkeypatch):
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _Completed(2))

    assert _backup.run_backup() is False


def test_run_backup_absorbs_a_failure_to_run_at_all(monkeypatch):
    """A timeout or a missing interpreter must not escape into the app."""
    def explode(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="bash", timeout=1)

    monkeypatch.setattr(subprocess, "run", explode)

    assert _backup.run_backup() is False


def test_backup_loop_takes_no_dump_if_stopped_during_the_initial_delay(monkeypatch):
    monkeypatch.setattr(_backup, "run_backup", lambda: 1 / 0)
    stop = threading.Event()
    stop.set()

    assert _backup.backup_loop(stop, interval=99, delay=99) == 0


def test_backup_loop_dumps_then_stops_when_the_event_is_set(monkeypatch):
    """One dump per tick, and a stop is acted on rather than slept through."""
    attempts = []

    stop = threading.Event()

    def fake_backup():
        attempts.append(1)
        stop.set()          # ask for shutdown from inside the first dump

    monkeypatch.setattr(_backup, "run_backup", fake_backup)

    assert _backup.backup_loop(stop, interval=99, delay=0) == 1
    assert attempts == [1]


def test_backup_loop_keeps_dumping_until_it_is_stopped(monkeypatch):
    """The schedule is a loop, not a one-shot: it survives its first tick."""
    attempts = []
    stop = threading.Event()

    def fake_backup():
        attempts.append(1)
        if len(attempts) == 2:
            stop.set()

    monkeypatch.setattr(_backup, "run_backup", fake_backup)

    assert _backup.backup_loop(stop, interval=0, delay=0) == 2


def test_start_backup_scheduler_starts_nothing_when_disabled(monkeypatch):
    """The verification app runs with this off — see config/backup.py."""
    monkeypatch.setattr(_backup, "BACKUP_ENABLED", False)

    assert _backup.start_backup_scheduler() is None


def test_start_backup_scheduler_runs_a_daemon_thread(monkeypatch):
    monkeypatch.setattr(_backup, "BACKUP_ENABLED", True)
    monkeypatch.setattr(_backup, "run_backup", lambda: None)

    stop = _backup.start_backup_scheduler(interval=0.01, delay=0)
    try:
        assert stop is not None
        thread = next(t for t in threading.enumerate()
                      if t.name == _backup.THREAD_NAME)
        # A daemon, so it dies with the process that owns the schedule.
        assert thread.daemon is True
    finally:
        stop.set()
