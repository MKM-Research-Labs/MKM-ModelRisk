# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
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
