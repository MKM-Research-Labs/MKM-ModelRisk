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
"""On-disk store for uploaded files (logos, meeting documents)."""
from __future__ import annotations

from pathlib import Path

from werkzeug.utils import secure_filename

from config.files import ALLOWED_UPLOAD_EXTENSIONS, MAX_UPLOAD_BYTES, UPLOAD_DIR


class UploadError(ValueError):
    """Raised when an upload is rejected (bad extension or too large)."""


def extension(name: str) -> str:
    return name.rsplit(".", 1)[-1].lower() if "." in name else ""


def save_upload(scope: str, original_name: str, data: bytes, base: Path | None = None) -> dict:
    """Validate and store ``data`` under ``<base>/<scope>/``; return metadata."""
    ext = extension(original_name)
    if ext not in ALLOWED_UPLOAD_EXTENSIONS:
        raise UploadError(f"file type not allowed: {ext or 'unknown'}")
    if len(data) > MAX_UPLOAD_BYTES:
        raise UploadError("file exceeds the maximum allowed size")
    safe = secure_filename(original_name)
    target_dir = (base or UPLOAD_DIR) / scope
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / safe).write_bytes(data)
    return {"filename": safe, "original_name": original_name}


def upload_path(scope: str, filename: str, base: Path | None = None) -> Path:
    """The on-disk path for a stored file (sanitised)."""
    return (base or UPLOAD_DIR) / scope / secure_filename(filename)
