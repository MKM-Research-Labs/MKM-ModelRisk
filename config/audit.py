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
"""Coding-rule audit thresholds and scan scope (coding rule R1)."""
from __future__ import annotations

from pathlib import Path

from config.database import DatabaseConfig
from config.files import UPLOAD_DIR

# Where generated audit report PDFs are written: under the configured upload
# directory, so generated state follows UPLOAD_DIR wherever an operator points it
# rather than being written into the checkout. Scoped by the active database name
# so reports from different databases (e.g. the dev vs. the pre-seeded demo DB)
# never overwrite or masquerade as one another.
AUDIT_OUTPUT_DIR = UPLOAD_DIR / "audit" / DatabaseConfig.from_env().name

# The user guide (Markdown) — published as a PDF into the Audit Reports tab.
USER_GUIDE_MD = Path(__file__).resolve().parents[1] / "docs" / "user_guide.md"

# Test-evidence artefacts produced by the audit run itself and written into
# AUDIT_OUTPUT_DIR alongside the report PDFs — mirroring PhysicalRisk, where the
# audit run drops coverage, JUnit and the test-summary artefacts into one place.
JUNIT_XML_NAME = "junit.xml"
COVERAGE_XML_NAME = "coverage.xml"
COVERAGE_HTML_DIRNAME = "coverage"          # holds index.html + static assets
E2E_JUNIT_XML_NAME = "e2e_junit.xml"
INIT_AUDIT_JSON_NAME = "init_audit_results.json"
TEST_REPORT_PDF_NAME = "test_report.pdf"
COMPLETENESS_REPORT_PDF_NAME = "completeness_audit.pdf"
JSON_FILES_REPORT_PDF_NAME = "json_files_report.pdf"

# Human-readable titles for the generated report files (filename -> label).
AUDIT_REPORT_LABELS = {
    "coding_rule_audit.pdf": "Coding-Rule Audit",
    "model_risk_report.pdf": "Model Risk Report",
    COMPLETENESS_REPORT_PDF_NAME: "Governance Completeness Audit",
    "user_guide.pdf": "User Guide",
    TEST_REPORT_PDF_NAME: "Test Report",
    JSON_FILES_REPORT_PDF_NAME: "JSON-File Audit",
    JUNIT_XML_NAME: "JUnit Results",
    E2E_JUNIT_XML_NAME: "E2E JUnit Results",
    COVERAGE_XML_NAME: "Coverage (Cobertura XML)",
    INIT_AUDIT_JSON_NAME: "__init__ Audit (JSON)",
}

# Label for the browsable HTML coverage report (a directory, surfaced as one card).
COVERAGE_HTML_LABEL = "Coverage HTML"

# Coding rule R2: source files should stay under this many lines.
MAX_SOURCE_FILE_LINES = 300
MAX_TEST_FILE_LINES = 400

# Directories scanned for source-code audits, and the source-of-truth for params.
SOURCE_DIRS = ("config", "src", "scripts", "app")
CONFIG_DIR = "config"

# Every first-party sub-tree. Coding rule R5 ("every first-party .py and .js
# file") is licence-bearing scope, so it is repo-wide like R2's: root-level files
# (model.py) plus these trees — tests, docs, the published packages/ clients and the
# contracts/ schemas included. Scoping it to SOURCE_DIRS would let the entry point,
# the test suite and a shipped package carry a stale licence while R5 passed.
FIRST_PARTY_DIRS = ("config", "src", "scripts", "audit", "tests", "docs",
                    "packages", "contracts")

# The header gate (audit/headers.py) and the notice scan (audit/notices.py) share
# that scope: between them they must account for every first-party file.
HEADER_SCAN_DIRS = FIRST_PARTY_DIRS
HEADER_EXTENSIONS = (".py", ".js")

# Licence notices on everything R5's full-block gate does not cover (.sql, .css,
# .html, .sh, .md, .toml, .txt, dotfiles, images, binaries). Those files carry a
# one-line notice in their own comment syntax rather than the 19-line block; the
# notice audit is reported, not gating, because the wording is prose and the
# comment syntax varies. A file that cannot hold a comment at all (JSON forbids
# them; binaries have no syntax) is marked by a sibling ``<name>.license`` file,
# REUSE-style — so it is recorded as decided, never as overlooked.
NOTICE_MARKER = "MIT License"
NOTICE_SIBLING_SUFFIX = ".license"

# Files that state the licence rather than reference it, so they need no notice.
NOTICE_EXEMPT_NAMES = frozenset({"LICENSE"})

# Generated or local-only files (mirrors the .gitignore entries that name files
# rather than directories, which EXCLUDE_DIRS already covers). Not first-party,
# so the notice scan never reports — or reads — them. ``.env`` holds secrets.
NOTICE_EXCLUDE_NAMES = frozenset({".DS_Store", ".coverage", "coverage.xml", ".env"})
# Local-only notes (gitignored via ``*.local.md``, e.g. internal planning that is
# never committed) are not first-party artefacts, so the notice scan skips them.
LOCAL_ONLY_SUFFIX = ".local.md"

# Package trees scanned for the R4 ``__init__.py`` inventory. Broader than
# SOURCE_DIRS so the inventory lists every first-party package initialiser —
# including the audit suite and the bundled packages/ — not just the app source.
INIT_INVENTORY_DIRS = ("config", "src", "scripts", "app", "audit", "packages")

# Coding rule R2 — the "split rule". The modularisation scan is repo-wide: it
# covers all non-test first-party code (root-level files like model.py plus these
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
    # Gitignored, third-party material that is never part of the source tree:
    # "local" holds machine-only scripts and database dumps, "bib"/"Bib" the
    # reference PDFs uploaded into the app. Neither is first-party, so no rule
    # (least of all the licence-notice scan) should read or report them.
    "local", "bib", "Bib",
})

# Coding rule R6 (JSON-file audit) — MKM-ModelRisk persists through the Postgres
# event store, so first-party source should not read or write ``.json`` files on
# disk. The json-file audit flags ``json.load``/``json.dump`` calls and ``.json``
# path literals under the source dirs; it is reported (non-gating), tracking the
# json→Postgres migration backlog. Files whose basename is allowlisted here are
# config/manifest artefacts (not runtime data stores) and are not flagged.
JSON_IO_ALLOWLIST = frozenset({
    "package.json", "package-lock.json", "pyproject.toml", "tsconfig.json",
})

# Duplicate-code detection (jscpd).
JSCPD_MIN_LINES = 8
JSCPD_MIN_TOKENS = 50
DUPLICATION_MAX_PERCENT = 5.0

# Coverage gate (mirrors pyproject's fail_under).
COVERAGE_MINIMUM = 99
