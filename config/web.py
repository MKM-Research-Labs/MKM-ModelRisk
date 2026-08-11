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
"""Web server configuration (coding rule R1).

Covers both entry points: the Werkzeug development server (``python model.py``,
auto-reloading, single process) and the WSGI server that serves the real thing
(``gunicorn`` against ``wsgi:application``). Everything gunicorn is told comes
from here — ``gunicorn.conf.py`` only wires these names to gunicorn's own.
"""
from __future__ import annotations

import os

WEB_HOST = os.environ.get("WEB_HOST", "127.0.0.1")
WEB_PORT = int(os.environ.get("WEB_PORT", "5015"))

# The socket gunicorn listens on, as gunicorn spells it.
WEB_BIND = os.environ.get("WEB_BIND", f"{WEB_HOST}:{WEB_PORT}")

# Worker model. ``gthread`` rather than the default sync worker: requests here
# spend most of their time waiting on PostgreSQL, and threads absorb that far
# more cheaply than processes. Connections are opened and closed per call
# (src/database/_connection.py) with no shared pool, so nothing is shared across
# a worker's threads and nothing survives the fork.
WEB_WORKER_CLASS = os.environ.get("WEB_WORKER_CLASS", "gthread")

# Deliberately modest, and NOT the usual (2 x cores) + 1. Peak connections to
# PostgreSQL are workers x threads, against a cluster whose max_connections is
# the stock 100 — the default formula on a many-core machine would exhaust it.
WEB_WORKERS = int(os.environ.get("WEB_WORKERS", "4"))
WEB_THREADS = int(os.environ.get("WEB_THREADS", "4"))

# Generous on purpose: generating the audit-report and Model Risk Report PDFs
# shells out to tectonic, which takes far longer than gunicorn's stock 30s.
# Under that default the worker would be killed mid-render and the request would
# fail as a bare 502 with nothing in the log to explain it.
WEB_TIMEOUT = int(os.environ.get("WEB_TIMEOUT", "300"))

# How long an old worker may finish in-flight requests during a restart.
WEB_GRACEFUL_TIMEOUT = int(os.environ.get("WEB_GRACEFUL_TIMEOUT", "30"))

# ``-`` is gunicorn's spelling of "the standard streams", matching how the dev
# server logs today, so the start scripts and the console behave the same way.
WEB_ACCESS_LOG = os.environ.get("WEB_ACCESS_LOG", "-")
WEB_ERROR_LOG = os.environ.get("WEB_ERROR_LOG", "-")
WEB_LOG_LEVEL = os.environ.get("WEB_LOG_LEVEL", "info")

# Set in the gunicorn master once the one-time startup work (migrations, seeded
# defaults, read-model rebuild) has been done, and inherited across the fork so
# each worker knows to skip it. See src/web/_startup.py and gunicorn.conf.py.
BOOTSTRAP_DONE_ENV = "MODELRISK_BOOTSTRAP_DONE"
