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
"""Over-long file audit (coding rule R2): files should split into packages."""
from __future__ import annotations

from pathlib import Path

from config.audit import MAX_SOURCE_FILE_LINES, MAX_TEST_FILE_LINES, SOURCE_DIRS

from audit._walk import count_lines, py_files, rel, walk, REPO_ROOT


def _scan(paths, limit: int) -> list[dict]:
    findings = []
    for path in paths:
        lines = count_lines(path)
        if lines > limit:
            findings.append({"path": rel(path), "lines": lines, "limit": limit})
    return sorted(findings, key=lambda f: f["lines"], reverse=True)


def large_source_files(limit: int = MAX_SOURCE_FILE_LINES) -> list[dict]:
    """Non-test ``.py`` files exceeding the source line limit."""
    return _scan(py_files(*SOURCE_DIRS), limit)


def large_test_files(limit: int = MAX_TEST_FILE_LINES) -> list[dict]:
    """Test ``.py`` files exceeding the (higher) test line limit."""
    return _scan(walk(REPO_ROOT / "tests", ".py"), limit)
