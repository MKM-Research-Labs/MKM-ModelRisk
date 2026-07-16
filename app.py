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
e.g. ``gunicorn app:app``.

``python app.py demo`` serves a separate, pre-seeded ``mkm_modelrisk_demo``
database (created and seeded on first run) — for client demos, never touching
the dev data.
"""
from __future__ import annotations

import os
import sys

_DEMO = len(sys.argv) > 1 and sys.argv[1] == "demo"
if _DEMO:
    os.environ["MKM_DB_NAME"] = "mkm_modelrisk_demo"

from config.web import WEB_HOST, WEB_PORT  # noqa: E402
from src.web import create_app  # noqa: E402

if _DEMO:
    from scripts.demo import bootstrap_demo  # noqa: E402

    bootstrap_demo()
    app = create_app(run_db_migrations=False)
else:
    app = create_app()

if __name__ == "__main__":  # pragma: no cover
    app.run(host=WEB_HOST, port=WEB_PORT, debug=not _DEMO)
