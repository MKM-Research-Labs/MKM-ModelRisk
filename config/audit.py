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

from pathlib import Path

from config.database import DatabaseConfig

# Where generated audit report PDFs are written (under the gitignored uploads/).
# Scoped by the active database name so reports from different databases (e.g.
# the dev vs. the pre-seeded demo DB) never overwrite or masquerade as one
# another — they share this fixed path but should not share files.
AUDIT_OUTPUT_DIR = (
    Path(__file__).resolve().parents[1] / "uploads" / "audit" / DatabaseConfig.from_env().name
)

# The user guide (Markdown) — published as a PDF into the Audit Reports tab.
USER_GUIDE_MD = Path(__file__).resolve().parents[1] / "docs" / "user_guide.md"

# Human-readable titles for the generated report files (filename -> label).
AUDIT_REPORT_LABELS = {
    "coding_rule_audit.pdf": "Coding-Rule Audit",
    "model_risk_report.pdf": "Model Risk Report",
    "user_guide.pdf": "User Guide",
}

# Coding rule R2: source files should stay under this many lines.
MAX_SOURCE_FILE_LINES = 300
MAX_TEST_FILE_LINES = 400

# Directories scanned for source-code audits, and the source-of-truth for params.
SOURCE_DIRS = ("config", "src", "scripts", "app")
CONFIG_DIR = "config"

# Coding rule R2 — the "split rule". The modularisation scan is repo-wide: it
# covers all non-test first-party code (root-level files like app.py plus these
# sub-trees), not just SOURCE_DIRS, so the docs/ generators and web assets are
# held to the same size limit. Tests are excluded — they carry their own,
# higher limit and their own scan (large_test_files).
REPO_SCAN_DIRS = ("config", "src", "scripts", "app", "docs")

# Web assets (JS/CSS) are audited for over-length separately from Python: they
# share the source line limit but are reported, not gated, so a long vendored or
# generated bundle never fails the Python size gate.
WEB_EXTENSIONS = (".js", ".css")

# Coding rule R6 — data-store access. The one package allowed to hold SQL, ORM
# sessions, DB drivers or connection/cursor handles; every other module reaches
# the store through its public API. The data-access audit flags usage outside it.
DATABASE_PACKAGE = "src/database"

# Path-definition audit — the one package allowed to define filesystem paths
# (the project root and the on-disk data trees). Modules elsewhere obtain
# directories from it rather than hand-deriving the root or hard-coding paths.
PATH_CONFIG_PACKAGE = "config"

# On-disk data-tree directory names owned by config (MKM stores generated files
# and uploads under uploads/). A path literal or segment naming one of these,
# built outside PATH_CONFIG_PACKAGE, is a path-definition finding.
DATA_TREE_NAMES = ("uploads",)

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
