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
"""Tests for the on-disk upload store."""
from __future__ import annotations

import pytest

from src.files import UploadError, save_upload, upload_path


def test_save_and_read_round_trip(tmp_path):
    meta = save_upload("mrc", "Logo.PNG", b"abc", base=tmp_path)
    assert meta["original_name"] == "Logo.PNG"
    assert upload_path("mrc", meta["filename"], base=tmp_path).read_bytes() == b"abc"


def test_accepts_latex_source(tmp_path):
    """A generated document's .tex is filed alongside its PDF as the auditable
    original; uploads are stored and served back, never compiled."""
    meta = save_upload("mrc", "handover.tex", rb"\documentclass{article}", base=tmp_path)
    assert meta["original_name"] == "handover.tex"


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
