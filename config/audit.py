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

# The integration guide (LaTeX) — how the platform works, how to restyle it, how to
# move it to another SQL engine or a container, and how it takes identity from an
# SSO. Published as a PDF into the Audit Reports tab beside the user guide.
INTEGRATION_GUIDE_TEX = (
    Path(__file__).resolve().parents[1] / "docs" / "integration_guide.tex"
)
INTEGRATION_GUIDE_PDF_NAME = "integration_guide.pdf"

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

# Coordination files for the background refresh, written into AUDIT_OUTPUT_DIR.
# Both are dotfiles so ``catalogue()`` leaves them out of the tab. They live on
# disk rather than in memory because the console runs under gunicorn with several
# workers: a module-level flag is per-process, so the worker answering the status
# poll is usually not the worker running the refresh, and a lock held in one
# worker does not serialise a second worker rendering into the same directory.
REFRESH_STATE_NAME = ".refresh_state.json"
REFRESH_WRITE_LOCK_NAME = ".refresh_write.lock"

# How long one suite invocation may take before the refresh gives up on it. The
# unit suite alone runs for roughly fourteen minutes and the audit's variant also
# writes the browsable HTML coverage tree, so the old 900s sat close enough to the
# real time that a busy machine tipped it over -- and a timed-out run writes no
# coverage.xml at all, leaving the R3 table showing the previous run's numbers with
# nothing on the page to say the refresh had failed. Generous rather than tight:
# this runs in the background, so waiting costs nothing and giving up costs the
# report.
SUITE_TIMEOUT_SECONDS = 2400

# What the status endpoint reports when the refresh's owning process is gone --
# killed, restarted or crashed. Without it an interrupted run is indistinguishable
# from a finished one, and the tab presents stale artefacts as fresh output.
REFRESH_INTERRUPTED = ("The background refresh stopped before it finished "
                       "(the server process it was running in went away). "
                       "Coverage, JUnit and the Test Report may be out of date.")

# Human-readable titles for the generated report files (filename -> label).
AUDIT_REPORT_LABELS = {
    "coding_rule_audit.pdf": "Coding-Rule Audit",
    "model_risk_report.pdf": "Model Risk Report",
    COMPLETENESS_REPORT_PDF_NAME: "Governance Completeness Audit",
    "user_guide.pdf": "User Guide",
    # The editable form of the same guide, named apart from the PDF because the
    # two now sit side by side under the User sub-tab.
    "user_guide.docx": "User Guide (Word)",
    INTEGRATION_GUIDE_PDF_NAME: "Integration Guide",
    TEST_REPORT_PDF_NAME: "Test Report",
    JSON_FILES_REPORT_PDF_NAME: "JSON-File Audit",
    JUNIT_XML_NAME: "JUnit Results",
    E2E_JUNIT_XML_NAME: "E2E JUnit Results",
    COVERAGE_XML_NAME: "Coverage (Cobertura XML)",
    INIT_AUDIT_JSON_NAME: "__init__ Audit (JSON)",
}

# Label for the browsable HTML coverage report (a directory, surfaced as one card).
COVERAGE_HTML_LABEL = "Coverage HTML"

# --- Audit Reports tab: the two sub-tabs an artefact appears under ----------------
# The tab is read by two audiences that share nothing but the Generate button: whoever
# governs the estate (its own reports, and the guides), and whoever maintains the code
# (the R1-R10 rule evidence and the test artefacts). USER_FOCUSED_REPORTS names the
# first set; everything else falls to DEFAULT_REPORT_GROUP, so a report added for a new
# numbered rule lands under Code without being listed here.
USER_FOCUSED_REPORTS = (
    "model_risk_report.pdf",
    COMPLETENESS_REPORT_PDF_NAME,
    "user_guide.pdf",
    "user_guide.docx",
    INTEGRATION_GUIDE_PDF_NAME,
)
USER_REPORT_GROUP = "user"
DEFAULT_REPORT_GROUP = "code"

# Coding rule R2: source files should stay under this many lines.
MAX_SOURCE_FILE_LINES = 300
MAX_TEST_FILE_LINES = 400

# Directories scanned for source-code audits, and the source-of-truth for params.
SOURCE_DIRS = ("config", "src", "scripts")
CONFIG_DIR = "config"

# --- Coding rule R10: where a colour may be written down -------------------------
# The one module allowed to name a colour. Everything else refers to a token.
THEME_MODULE = "config/theme.py"

# The front-end trees scanned for colour literals and token references.
STYLING_ASSET_DIRS = ("src/static", "src/templates")

# Suffixes whose colour literals are a GATED finding. Every front-end surface is
# converted as of step 5 of docs/design/theme_config.md, so all three are gated and
# the reported backlog is empty. A colour typed into any of them now fails the audit.
STYLING_GATED_SUFFIXES = (".css", ".html", ".js")

# Package trees scanned for the R4 ``__init__.py`` inventory. Broader than
# SOURCE_DIRS so the inventory lists every first-party package initialiser —
# including the audit suite and the bundled packages/ — not just the app source.
INIT_INVENTORY_DIRS = ("config", "src", "scripts", "audit", "packages")

# All three directory lists above and below also carried "app" — a directory that
# has never existed in this repository, in any commit. It scanned nothing, which
# is indistinguishable from scanning something clean, and it made the lists look
# maintained. Removed 2026-09-05; a test now asserts every entry names a real
# directory (tests/audit/test_audit_scan_roots.py).

# Coding rule R2 — the "split rule". The modularisation scan is repo-wide: it
# covers all non-test first-party code (root-level files like model.py plus these
# sub-trees), not just SOURCE_DIRS, so the docs/ generators and web assets are
# held to the same size limit. Tests are excluded — they carry their own,
# higher limit and their own scan (large_test_files).
#
# "Repo-wide" was not true of this list until 2026-09-05: audit/, packages/ and
# modelrisk/ were absent, so the audit suite was the one tree its own rules did
# not reach — and audit/pdf.py had grown to 312 lines unreported. The tool that
# measures the codebase is part of the codebase. INIT_INVENTORY_DIRS below had
# the wider list all along, which is how the omission stayed invisible: the two
# constants sat adjacent and disagreed.
REPO_SCAN_DIRS = ("config", "src", "scripts", "docs", "audit", "packages",
                  "modelrisk")

# Web assets (JS/CSS) are audited for over-length separately from Python, and share
# the source line limit. They were reported rather than gated so that a long vendored
# or generated bundle could never fail the size gate — but this console has no bundle:
# all 83 assets are hand-written first-party source, and node_modules is excluded
# above. The exemption was protecting against something that is not here, while
# thirteen hand-written files sat over the limit.
#
# Gated since 2026-09-05, from a backlog of zero. If a vendored or minified asset is
# ever added, exclude it deliberately — a build directory in EXCLUDE_DIRS, say —
# rather than standing the whole rule down again.
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
