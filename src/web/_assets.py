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
"""Cache-busting stamp for the console's own CSS and JavaScript.

``Cache-Control: no-store`` asks a browser not to keep a copy, but it is a request
and not a guarantee: a browser that cached an asset under an earlier, more
permissive policy keeps serving that copy, and the user sees a console built from
JavaScript that no longer matches the server. The symptom is a feature that exists
in the code, is served correctly over HTTP, and is still missing on screen.

Appending a stamp that changes whenever a file changes makes the URL itself new, so
there is no prior copy to serve and the question cannot arise.
"""
from __future__ import annotations

from pathlib import Path

from config.paths import STATIC_DIR

# The extensions the console loads through ``url_for('static', ...)``. Images are
# excluded: the logo is served from an API route, not from here.
ASSET_SUFFIXES = (".js", ".css")


def asset_version(static_dir: Path | None = None) -> str:
    """A stamp for the current state of the static assets.

    The newest modification time across every served asset, as an integer. It moves
    whenever any file is edited (including a checkout that restores an older file,
    which also updates the mtime), and is stable across restarts when nothing has
    changed, so browsers keep their copies while the assets really are unchanged.
    """
    root = STATIC_DIR if static_dir is None else static_dir
    times = [path.stat().st_mtime for path in root.rglob("*")
             if path.suffix in ASSET_SUFFIXES and path.is_file()]
    return str(int(max(times))) if times else "0"
