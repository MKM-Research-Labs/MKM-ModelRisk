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
"""Audit gate: over-long files (coding rule R2)."""
from __future__ import annotations

from audit.large_files import large_source_files, large_test_files, large_web_files


def test_threshold_excludes_when_limit_is_high():
    assert large_source_files(limit=100_000) == []
    assert large_web_files(limit=100_000) == []


def test_scan_orders_by_line_count_descending():
    found = large_source_files(limit=1)  # every source file exceeds one line
    assert found
    assert found == sorted(found, key=lambda f: f["lines"], reverse=True)


def test_source_tree_within_limit():
    # Coding rule R2 hard gate: no source file exceeds 300 lines.
    assert large_source_files() == []


def test_test_suite_stays_within_limit():
    # Coding rule R2 gate for test files (<= 400 lines).
    assert large_test_files() == []


def test_test_file_scanner_detects_oversize():
    assert large_test_files(limit=1)  # all test files exceed one line


def test_web_scanner_orders_by_line_count_descending():
    # Reported (non-gating): with a tiny limit every web asset is over-length,
    # and findings come back sorted by size descending like the source scan.
    found = large_web_files(limit=1)
    assert found
    assert found == sorted(found, key=lambda f: f["lines"], reverse=True)
    assert all(f["path"].endswith((".js", ".css")) for f in found)
