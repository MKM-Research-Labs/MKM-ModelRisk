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
"""Over-long file audit (coding rule R2): files should split into packages.

The "split rule": every non-test source file should stay under the size limit,
splitting into a package of focused modules once it grows past it. The scan is
repo-wide — root-level files plus ``REPO_SCAN_DIRS`` (src/, config/, scripts/,
app/ and the docs/ generators) — so no first-party Python escapes the limit by
living outside ``src/``. Web assets (JS/CSS) are held to the same limit but
reported separately via ``large_web_files`` (not gated).
"""
from __future__ import annotations

from config.audit import (
    MAX_SOURCE_FILE_LINES,
    MAX_TEST_FILE_LINES,
    REPO_SCAN_DIRS,
    WEB_EXTENSIONS,
)

from audit._walk import code_files, count_lines, rel, walk, REPO_ROOT


def _scan(paths, limit: int) -> list[dict]:
    findings = []
    for path in paths:
        lines = count_lines(path)
        if lines > limit:
            findings.append({"path": rel(path), "lines": lines, "limit": limit})
    return sorted(findings, key=lambda f: f["lines"], reverse=True)


def large_source_files(limit: int = MAX_SOURCE_FILE_LINES) -> list[dict]:
    """Non-test ``.py`` files, repo-wide, exceeding the source line limit."""
    return _scan(code_files(REPO_SCAN_DIRS, (".py",)), limit)


def large_web_files(limit: int = MAX_SOURCE_FILE_LINES) -> list[dict]:
    """Web assets (``.js`` / ``.css``), repo-wide, over the source line limit.

    Reported for visibility rather than gated: a long generated or vendored
    bundle should not fail the build, but oversized hand-written UI scripts are
    split candidates just like Python modules.
    """
    return _scan(code_files(REPO_SCAN_DIRS, WEB_EXTENSIONS), limit)


def large_test_files(limit: int = MAX_TEST_FILE_LINES) -> list[dict]:
    """Test ``.py`` files exceeding the (higher) test line limit."""
    return _scan(walk(REPO_ROOT / "tests", ".py"), limit)
