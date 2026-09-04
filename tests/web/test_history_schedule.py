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
memory of its own. What matters here is the same thing that matters for the backup
schedule: a failed look costs a gap in the series, and a gap is a far smaller thing
than an observer that took the console down with it.
"""
from __future__ import annotations

import threading

from src.governance import attention
from src.web import _history


def test_an_observation_records_a_look_and_reports_success(monkeypatch):
    looked = []
    monkeypatch.setattr(attention, "observe", lambda: looked.append(1) or {"seen": 1})

    assert _history.run_observation() is True
    assert looked == [1]


def test_an_observation_that_raises_is_absorbed_rather_than_propagated(monkeypatch):
    """A scan that raised, or a database that was down, costs one day of the series
    and nothing else."""
    def explode():
        raise RuntimeError("the completeness scan blew up")
    monkeypatch.setattr(attention, "observe", explode)

    assert _history.run_observation() is False


def test_nothing_is_observed_if_the_schedule_is_stopped_during_its_first_delay():
    stop = threading.Event()
    stop.set()

    assert _history.history_loop(stop, interval=99, delay=99) == 0


def test_the_loop_looks_once_per_tick_and_acts_on_a_stop_at_once(monkeypatch):
    """Waiting on the event rather than sleeping is why a shutdown is not slept
    through for the rest of a day."""
    attempts = []
    stop = threading.Event()

    def observe_once():
        attempts.append(1)
        stop.set()          # ask for shutdown from inside the first observation
    monkeypatch.setattr(_history, "run_observation", observe_once)

    assert _history.history_loop(stop, interval=99, delay=0) == 1


def test_the_schedule_survives_its_first_tick(monkeypatch):
    attempts = []
    stop = threading.Event()

    def observe_twice():
        attempts.append(1)
        if len(attempts) == 2:
            stop.set()
    monkeypatch.setattr(_history, "run_observation", observe_twice)

    assert _history.history_loop(stop, interval=0, delay=0) == 2


def test_no_thread_is_started_when_the_history_is_turned_off(monkeypatch):
    """Turned off, the trend and the finding ages stay empty — which is a stated
    outcome rather than a silent one."""
    monkeypatch.setattr(_history, "HISTORY_ENABLED", False)

    assert _history.start() is None


def test_the_schedule_runs_in_a_daemon_thread(monkeypatch):
    """Daemon, so a process that simply exits is not held open by the observer."""
    monkeypatch.setattr(_history, "HISTORY_ENABLED", True)
    monkeypatch.setattr(_history, "HISTORY_STARTUP_DELAY_SECONDS", 99)
    stop = threading.Event()

    thread = _history.start(stop)
    assert thread is not None and thread.daemon
    assert thread.name == _history.THREAD_NAME
    stop.set()
    thread.join(timeout=5)
    assert not thread.is_alive()
