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
"""Gunicorn settings — picked up automatically when run from the repo root.

Every value comes from ``config/web.py`` (coding rule R1: parameters have one
home); this file only spells them the way gunicorn does. Run it with:

    gunicorn wsgi:application

The hooks below are the substance. Two things used to happen once because the
app was one process, and would otherwise silently become per-worker:

* the startup work — migrations, seeded defaults, the read-model rebuild;
* the hourly database backup.

Both now run in the master, before the fork. The backup thread does not survive
into the workers (``fork`` carries only the calling thread), which is exactly
what is wanted: one schedule, owned by the process that outlives worker
recycling.
"""
from config.web import (WEB_ACCESS_LOG, WEB_BIND, WEB_CONTROL_SOCKET, WEB_ERROR_LOG,
                        WEB_GRACEFUL_TIMEOUT, WEB_LOG_LEVEL, WEB_PROC_NAME,
                        WEB_THREADS, WEB_TIMEOUT, WEB_WORKER_CLASS, WEB_WORKERS)

bind = WEB_BIND
workers = WEB_WORKERS
threads = WEB_THREADS
worker_class = WEB_WORKER_CLASS
timeout = WEB_TIMEOUT
graceful_timeout = WEB_GRACEFUL_TIMEOUT
accesslog = WEB_ACCESS_LOG
errorlog = WEB_ERROR_LOG
loglevel = WEB_LOG_LEVEL

# One identity per app, keyed on its database. Without these the estate's app and the
# verification app are the same command twice: the same ``pgrep -f`` pattern matches
# both, and both write gunicorn's default control socket. Killing "the verification
# app" could then kill the estate's -- see config/web.py for what that has cost.
proc_name = WEB_PROC_NAME
control_socket = WEB_CONTROL_SOCKET

# Each worker imports wsgi.py for itself. Preloading would build the app in the
# master and fork the result, which saves memory but is the wrong trade here:
# the master would hold an app it never serves with, and a worker could inherit
# state established at import. The startup work it would have saved is already
# done once, in the hook below.
preload_app = False


def on_starting(server):
    """Master process, before any worker is forked."""
    from src.web._backup import start_backup_scheduler
    from src.web._history import start as start_history_scheduler
    from src.web._startup import bootstrap_once

    # Marks the environment on completion; forked workers inherit that and skip
    # it, so the migration runner is never executed by several processes at once.
    bootstrap_once()

    # Started here, in the master, so there is exactly one backup schedule
    # however many workers are running. See src/web/_backup.py.
    start_backup_scheduler()

    # Likewise the daily finding-history observation: one per deployment, not one
    # per worker, or every worker would run a completeness scan at the same moment
    # every day. See src/web/_history.py.
    start_history_scheduler()
