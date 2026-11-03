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
"""Naming and checking a document filed as a link."""
from __future__ import annotations

import pytest

from src.files import UploadError
from src.governance.document_links import clean_link, link_name


def test_a_link_is_named_from_its_title_then_its_path_then_its_host():
    assert link_name("https://a.example.com/x/y", "Spec") == "Spec.url"
    assert link_name("https://a.example.com/x/y", "Spec.URL") == "Spec.URL"
    assert link_name("https://a.example.com/x/y/") == "y.url"
    assert link_name("https://a.example.com") == "a.example.com.url"


def test_an_address_is_trimmed_and_an_empty_one_refused():
    assert clean_link("  https://a.example.com/  ") == "https://a.example.com/"
    with pytest.raises(UploadError, match="no link"):
        clean_link("   ")
