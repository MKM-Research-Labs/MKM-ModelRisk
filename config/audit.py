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
"""Coding-rule audit thresholds and scan scope (coding rule R1)."""
from __future__ import annotations

# Coding rule R2: source files should stay under this many lines.
MAX_SOURCE_FILE_LINES = 300
MAX_TEST_FILE_LINES = 400

# Directories scanned for source-code audits, and the source-of-truth for params.
SOURCE_DIRS = ("config", "src", "scripts", "app")
CONFIG_DIR = "config"

# Directories never walked by any audit.
EXCLUDE_DIRS = frozenset({
    "__pycache__", ".git", ".venv", "node_modules", "uploads",
    ".pytest_cache", "htmlcov", "build", "dist", ".claude",
})

# Duplicate-code detection (jscpd).
JSCPD_MIN_LINES = 8
JSCPD_MIN_TOKENS = 50
DUPLICATION_MAX_PERCENT = 5.0

# Coverage gate (mirrors pyproject's fail_under).
COVERAGE_MINIMUM = 99
