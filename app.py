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
"""Application entry point.

Run the governance console with ``python app.py`` (applies DB migrations on
startup). ``app`` is exposed at module level so a WSGI server can serve it too,
e.g. ``gunicorn app:app``. ``python app.py phys`` populates the instance from the
PhysicalRisk model inventory (demo seed) instead of starting the server.
"""
from __future__ import annotations

import os
import sys

from config.web import WEB_HOST, WEB_PORT
from src.web import create_app

app = create_app()


def _start_backup_scheduler():  # pragma: no cover
    """Dump the database at startup and every hour while the app runs.

    In-app rather than a system scheduler: macOS blocks a background LaunchAgent
    from reading the repo under ~/Documents, but the app inherits the launching
    shell's permissions, so the backup script runs cleanly here. The thread is a
    daemon (dies with the process) and each run is best-effort — a failed or
    skipped backup (DB down, SSD unmounted) never disturbs the request loop.
    """
    import pathlib
    import subprocess
    import threading
    import time

    script = pathlib.Path(__file__).resolve().parent / "scripts" / "backup_db.sh"
    interval = int(os.environ.get("BACKUP_INTERVAL_SECONDS", "3600"))

    def loop():
        time.sleep(20)  # let migrations settle before the first snapshot
        while True:
            try:
                subprocess.run(["bash", str(script)], timeout=300, check=False)
            except Exception:
                pass
            time.sleep(interval)

    threading.Thread(target=loop, daemon=True, name="db-backup").start()


if __name__ == "__main__":  # pragma: no cover
    if sys.argv[1:2] == ["phys"]:
        from scripts.migrate_phys import main as seed_phys
        raise SystemExit(seed_phys())
    # Only in the reloader's worker child (WERKZEUG_RUN_MAIN), so the backup runs
    # once, not twice, under debug's auto-reloader.
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        _start_backup_scheduler()
    app.run(host=WEB_HOST, port=WEB_PORT, debug=True)
