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
"""Development entry point — the auto-reloading Werkzeug server.

``python model.py`` runs the console for local work: one process, debug on,
reloading as you edit. ``python model.py phys`` populates the instance from the
PhysicalRisk model inventory (demo seed) instead of starting the server.

This is not how the console is served for real. That is gunicorn against
``wsgi:application`` — see ``gunicorn.conf.py`` and ``scripts/start.sh``. The app
object is the same one, built in the same place (``wsgi.py``), so the two entry
points cannot drift apart; what differs is the server in front of it and, with
it, the debugger, the reloader and the single process.
"""
from __future__ import annotations

import os
import sys

from config.web import WEB_HOST, WEB_PORT
from wsgi import application as app  # noqa: F401 — re-exported for `gunicorn model:app`

if __name__ == "__main__":  # pragma: no cover
    if sys.argv[1:2] == ["phys"]:
        from scripts.migrate_phys import main as seed_phys
        raise SystemExit(seed_phys())
    # Only in the reloader's worker child (WERKZEUG_RUN_MAIN), so the backup runs
    # once, not twice, under debug's auto-reloader. Under gunicorn this is the
    # master's job instead — see on_starting in gunicorn.conf.py.
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        from src.web._backup import start_backup_scheduler
        start_backup_scheduler()
    app.run(host=WEB_HOST, port=WEB_PORT, debug=True)
