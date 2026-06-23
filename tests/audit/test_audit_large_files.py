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
"""Audit gate: over-long files (coding rule R2)."""
from __future__ import annotations

from audit.large_files import large_source_files, large_test_files


def test_threshold_excludes_when_limit_is_high():
    assert large_source_files(limit=100_000) == []


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
