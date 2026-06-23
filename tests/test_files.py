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
"""Tests for the on-disk upload store."""
from __future__ import annotations

import pytest

from src.files import UploadError, save_upload, upload_path


def test_save_and_read_round_trip(tmp_path):
    meta = save_upload("mrc", "Logo.PNG", b"abc", base=tmp_path)
    assert meta["original_name"] == "Logo.PNG"
    assert upload_path("mrc", meta["filename"], base=tmp_path).read_bytes() == b"abc"


def test_rejects_disallowed_extension(tmp_path):
    with pytest.raises(UploadError):
        save_upload("mrc", "evil.exe", b"x", base=tmp_path)


def test_rejects_no_extension(tmp_path):
    with pytest.raises(UploadError):
        save_upload("mrc", "noextension", b"x", base=tmp_path)


def test_rejects_oversized(tmp_path, monkeypatch):
    monkeypatch.setattr("src.files.store.MAX_UPLOAD_BYTES", 3)
    with pytest.raises(UploadError):
        save_upload("mrc", "a.txt", b"toolong", base=tmp_path)
