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
"""Filesystem path parameters (coding rule R1 — paths defined only in config).

The single home for repository-relative paths used by the migration runner and
the ingest validator, so no source or script module walks the tree with
``Path(__file__)`` itself.
"""
from __future__ import annotations

import os
from pathlib import Path

# Repository root (config/ lives directly under it).
_REPO_ROOT = Path(__file__).resolve().parents[1]

# Schema migration SQL, applied in lexical order by the migration runner.
MIGRATIONS_DIR = _REPO_ROOT / "src" / "database" / "migrations"

# Frozen v1 ingest contract schemas, loaded by the ingest validator.
CONTRACTS_V1_DIR = _REPO_ROOT / "contracts" / "ingest" / "v1"

# The console's served static assets (JS/CSS), fingerprinted for cache-busting.
STATIC_DIR = _REPO_ROOT / "src" / "static"

# The console's Jinja templates. The app factory points Flask at these folders
# relatively (rule R7); this is the absolute path, for the checks that read the
# front end as files and must not depend on the working directory — a worktree
# and the main checkout both have one, and a relative path finds the wrong tree.
TEMPLATES_DIR = _REPO_ROOT / "src" / "templates"

# The internal-disk backup script the app runs on a timer (see model.py).
BACKUP_SCRIPT = _REPO_ROOT / "scripts" / "backup_db.sh"

# Root of the producing repository a migration reads from. Machine-specific, so
# it comes from the environment; the default assumes it sits beside this clone,
# which is the usual layout. Never a hardcoded absolute path (rule R1).
PRODUCER_ROOT = Path(os.environ.get("PRODUCER_ROOT", str(_REPO_ROOT.parent / "PhysicalRisk")))

# The producing repo's model inventory — the source artifact the phys migration
# reads (models, collections, the declared chain).
PRODUCER_INVENTORY = (
    PRODUCER_ROOT / "docs" / "models" / "governance_data" / "model_inventory.json"
)

# Where the producing repo's portfolio generator ("port") leaves its output, read
# by ongoing monitoring to record what each model has been exercised against. One
# sub-directory per population group (here, a catchment).
#
# The trailing "input" is not a mistake: a generated portfolio is the *input* to
# every downstream model, so port writes its output there. An adopter whose
# generator writes elsewhere re-points this; if it resolves to nothing, the
# monitoring report says so rather than reporting an empty estate.
PRODUCER_PORTFOLIO_DIR = PRODUCER_ROOT / "data" / "input"
