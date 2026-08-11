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
"""WSGI entry point — the app as a real server serves it.

    gunicorn wsgi:application          # settings come from gunicorn.conf.py

This module is imported once per worker. The one-time startup work (migrations,
seeded defaults, read-model rebuild) has normally already been done by the
gunicorn master in ``on_starting``, which sets a marker in the environment that
every forked worker inherits — so ``bootstrap_once`` here is a no-op under
gunicorn and does the work under any other WSGI server that just imports this
module. Either way it happens before the first request, and the app itself is
then built with the startup work switched off.

``python model.py`` remains the development server: auto-reloading, one process,
debug on. It serves the same app object built the same way.
"""
from src.web import create_app
from src.web._startup import bootstrap_once

bootstrap_once()

# ``application`` is the WSGI standard name; ``app`` is the Flask convention.
application = create_app(run_db_migrations=False)
app = application
