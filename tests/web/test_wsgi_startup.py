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
"""The WSGI startup path: bootstrap once per boot, not once per worker.

Under gunicorn the master does the startup work before it forks and marks the
environment; every worker inherits the mark and skips it. These tests pin that
contract down, because getting it wrong is invisible in development — where
there is only ever one process — and shows up in production as workers racing
each other into the migration runner.
"""
from __future__ import annotations

import os
import runpy
from pathlib import Path

from config.web import BOOTSTRAP_DONE_ENV
from src.web import _startup
from src.web import app as app_module

GUNICORN_CONF = Path(__file__).resolve().parents[2] / "gunicorn.conf.py"


def test_bootstrap_runs_every_step_migrations_first_views_last(monkeypatch):
    called: list[str] = []

    monkeypatch.setattr("src.database.run_migrations",
                        lambda cfg=None: called.append("migrations"))
    for step in ("model_types", "reference_lists", "review_questions",
                 "standing_agenda", "status_vocabularies"):
        monkeypatch.setattr(f"src.governance.reference.ensure_default_{step}",
                            lambda name=step: called.append(name))
    monkeypatch.setattr(_startup, "reconcile_read_models",
                        lambda config=None: called.append("views"))

    _startup.bootstrap()

    # The schema has to exist before anything writes to it, and the views are
    # rebuilt from whatever the seeding just wrote.
    assert called[0] == "migrations"
    assert called[-1] == "views"
    assert set(called) == {"migrations", "model_types", "reference_lists",
                           "review_questions", "standing_agenda",
                           "status_vocabularies", "views"}


def test_bootstrap_once_does_the_work_and_marks_the_environment(monkeypatch):
    monkeypatch.delenv(BOOTSTRAP_DONE_ENV, raising=False)
    runs: list[int] = []
    monkeypatch.setattr(_startup, "bootstrap", lambda config=None: runs.append(1))

    assert _startup.bootstrap_once() is True
    assert runs == [1]
    # The mark is exactly what a forked worker inherits.
    assert os.environ[BOOTSTRAP_DONE_ENV] == "1"


def test_bootstrap_once_is_skipped_when_a_parent_already_did_it(monkeypatch):
    """A gunicorn worker must not repeat the master's startup work."""
    monkeypatch.setenv(BOOTSTRAP_DONE_ENV, "1")
    runs: list[int] = []
    monkeypatch.setattr(_startup, "bootstrap", lambda config=None: runs.append(1))

    assert _startup.bootstrap_once() is False
    assert runs == []


def test_create_app_without_migrations_runs_no_startup_work(monkeypatch):
    """What every worker does: build the app, repeat none of the startup work."""
    runs: list[int] = []
    monkeypatch.setattr(app_module, "bootstrap", lambda: runs.append(1))

    app_module.create_app(run_db_migrations=False)

    assert runs == []


def test_gunicorn_config_takes_every_setting_from_config_web():
    """gunicorn.conf.py is wiring only; the parameters live in config (rule R1)."""
    from config import web as web_config

    conf = runpy.run_path(str(GUNICORN_CONF))

    assert conf["bind"] == web_config.WEB_BIND
    assert conf["workers"] == web_config.WEB_WORKERS
    assert conf["threads"] == web_config.WEB_THREADS
    assert conf["worker_class"] == web_config.WEB_WORKER_CLASS
    assert conf["timeout"] == web_config.WEB_TIMEOUT
    assert conf["graceful_timeout"] == web_config.WEB_GRACEFUL_TIMEOUT
    # Preloading would build the app in the master and fork the result; the
    # workers are meant to build their own.
    assert conf["preload_app"] is False


def test_gunicorn_master_bootstraps_and_starts_one_backup_schedule(monkeypatch):
    """``on_starting`` is where "once per boot" is actually enforced."""
    conf = runpy.run_path(str(GUNICORN_CONF))
    done: list[str] = []

    monkeypatch.setattr(_startup, "bootstrap_once",
                        lambda config=None: done.append("bootstrap"))
    monkeypatch.setattr("src.web._backup.start_backup_scheduler",
                        lambda *args, **kwargs: done.append("backup"))

    conf["on_starting"](server=None)

    assert done == ["bootstrap", "backup"]
