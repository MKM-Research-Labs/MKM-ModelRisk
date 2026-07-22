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
"""File-upload configuration (coding rule R1)."""
from __future__ import annotations

import os
from pathlib import Path

# Where uploaded files (logos, meeting documents) are stored on disk.
UPLOAD_DIR = Path(
    os.environ.get("UPLOAD_DIR", str(Path(__file__).resolve().parents[1] / "uploads"))
)

# ``tex`` is allowed so a generated document can be filed alongside its PDF: the
# LaTeX source is the auditable original. Uploads are only ever stored and served
# back, never compiled, so no LaTeX is executed on the server.
ALLOWED_UPLOAD_EXTENSIONS = frozenset(
    {"pdf", "doc", "docx", "xls", "xlsx", "csv", "txt", "tex", "png", "jpg", "jpeg", "svg"}
)
IMAGE_EXTENSIONS = frozenset({"png", "jpg", "jpeg"})
MAX_UPLOAD_BYTES = 50 * 1024 * 1024

# Extensions a document may be served inline for (opened in a browser tab rather
# than downloaded). Deliberately narrow: an uploaded file rendered inline runs in
# this application's origin, so ``svg`` and any markup format are excluded -- an
# SVG can carry script. Everything else is still served, as a download.
INLINE_VIEW_EXTENSIONS = frozenset({"pdf", "png", "jpg", "jpeg", "txt"})

# Extensions kept on file but never listed in the console. The LaTeX source of a
# generated document is stored beside its PDF as the auditable original and can be
# replaced by re-uploading it, but listing both doubles every row for no reader.
HIDDEN_DOC_EXTENSIONS = frozenset({"tex"})
