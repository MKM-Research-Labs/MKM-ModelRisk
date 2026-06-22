# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Subsection 4.4: data-access governance audit (WP2.4 / json→postgres WP0.8).

A sibling to the path-definition audit (4.3). Policy: **all database access goes
through the one ``src/database`` utility package** — zero raw SQL, ORM sessions,
driver imports, or connection/cursor handles anywhere else; and the only place
that reads/writes the ``data/input/<catchment>`` JSON tree directly is the file
backend inside that package. Every other module obtains data through the
``database`` public API (``database.get_*`` / ``database.save_*``).

Two findings classes, deliberately gated differently:

* **DB-access** (``db_access`` findings) — a SQL keyword (``SELECT … FROM``,
  ``INSERT INTO``, ``UPDATE … SET``, ``DELETE FROM``, ``CREATE/ALTER/DROP
  TABLE``), ``.execute(`` / ``.executemany(``, a ``sqlalchemy`` / ``psycopg`` /
  ``asyncpg`` / ``sqlite3`` import, or a connection handle (``create_engine``,
  ``sessionmaker``, ``.cursor(``) found **outside** ``src/database``. This is the
  **zero-tolerance gate** — it is green by construction today (no Postgres
  backend exists yet) and must stay green as the backend lands in its private
  modules. Enforced by ``tests/commands/test_data_access_report.py``.

* **Direct file-I/O** (``file_io`` findings) — ``json.load`` / ``json.dump`` /
  ``open(`` / ``.glob(`` outside ``src/database``. This is a **tracked report,
  not a gate**: it measures how much of the JSON→repository migration remains
  (the un-migrated generators — property ts/hc, stressm, book, peril, typhoon —
  still read/write the tree directly). The count shrinks as later work packages
  move each reader onto the seam; it is surfaced for visibility, never failed.

The scan logic (``scan_repo`` / ``scan_text``) is exercised by the gate test, and
``_build_data_access`` renders the read-only compliance section for the
consolidated audit report.
"""

import os
import re
from pathlib import Path

from reportlab.lib.units import mm
from reportlab.platypus import HRFlowable, Paragraph, Spacer

from .._constants import NAVY, _root

# The sanctioned home for both SQL/connection code and direct data-tree file-I/O.
# Repo-relative POSIX prefix; any file beneath it is exempt from both scans.
SANCTIONED_PACKAGE = 'src/database'

# Directories never descended: tests (build their own scratch I/O), vendored
# code, caches, the ``data`` symlink to the shared SSD, infra, and worktrees.
_PRUNE_DIRS = {
    'tests',
    '.git', '.claude', '.claire', 'worktrees',
    '__pycache__', 'node_modules', '.venv', 'venv',
    'data', 'logs', 'docker', 'dist', 'build',
    '.pytest_cache', '.mypy_cache', '.ruff_cache',
}

# First-party files exempt by explicit, justified registration. Kept minimal.
_ALLOWLIST = {
    # (none yet — the DB-access gate is green by construction)
}

# ---------------------------------------------------------------------------
# Detection patterns
# ---------------------------------------------------------------------------

# --- DB-access (gated) -----------------------------------------------------
# Real SQL statements (structural, so prose like "update the set of …" or an
# identifier like ``delete_from_cache`` cannot match).
_SQL_RE = re.compile(
    r'\bSELECT\b[\s\S]*?\bFROM\b'
    r'|\bINSERT\s+INTO\b'
    r'|\bUPDATE\b[\s\S]*?\bSET\b'
    r'|\bDELETE\s+FROM\b'
    r'|\bCREATE\s+(?:TABLE|INDEX|SCHEMA|VIEW)\b'
    r'|\bALTER\s+TABLE\b'
    r'|\bDROP\s+(?:TABLE|INDEX|VIEW)\b',
    re.IGNORECASE,
)
# A cursor/connection executing a statement.
_EXEC_RE = re.compile(r'\.execute(?:many|script)?\s*\(')
# Importing a SQL driver / ORM.
_DRIVER_IMPORT_RE = re.compile(
    r'^\s*(?:import|from)\s+(?:sqlalchemy|psycopg2?|asyncpg|sqlite3|aiomysql|pymysql|MySQLdb)\b'
)
# Building an engine / session / cursor handle.
_CONN_RE = re.compile(r'\b(?:create_engine|sessionmaker|scoped_session)\s*\(|\.cursor\s*\(')

_DB_RULES = (
    ('sql', _SQL_RE),
    ('execute', _EXEC_RE),
    ('driver_import', _DRIVER_IMPORT_RE),
    ('connection', _CONN_RE),
)

# --- Direct file-I/O against the data tree (reported, not gated) -----------
_FILE_IO_RE = re.compile(r'\bjson\.(?:load|dump)s?\s*\(|(?<![\w.])open\s*\(|\.glob\s*\(')
# A file only counts toward the migration backlog if it *also* references the
# catchment data tree (a config data accessor or a ``data/`` path). This keeps
# incidental file-I/O — reading a license, a CSV from an external source, a
# config module — out of the migration metric, leaving only readers that should
# move onto the ``database`` seam.
_DATA_CONTEXT_RE = re.compile(
    r'\bget_input_dir\b|\bget_input_root\b|\bget_output_dir\b|\bget_reports_dir\b'
    r'|\bget_trading_dir\b|\bget_eod_dir\b|\bget_gaugets_dir\b|\bget_gaugehd_dir\b'
    r'|\bget_classifiers_dir\b|\bget_gaugehc_dir\b|\binput_dir\b|\boutput_dir\b'
    r'|data/input|data/output'
)


def iter_source_files(root: Path):
    """Yield every in-scope first-party ``.py`` file under *root*.

    Prunes tests/vendored/cache/worktree dirs and the shared ``data`` symlink,
    skips this scanner module (its source contains the very patterns it
    searches for), and skips the sanctioned ``src/database`` package."""
    root = Path(root)
    self_path = Path(__file__).resolve()
    sanctioned = (root / SANCTIONED_PACKAGE).resolve()
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in _PRUNE_DIRS]
        for name in filenames:
            if not name.endswith('.py'):
                continue
            path = Path(dirpath) / name
            rp = path.resolve()
            if rp == self_path:
                continue
            try:
                rp.relative_to(sanctioned)
                continue  # inside src/database — sanctioned
            except ValueError:
                pass
            yield path


def _rel(path: Path, root: Path) -> str:
    try:
        return Path(path).relative_to(root).as_posix()
    except ValueError:
        return Path(path).as_posix()


def scan_text(text: str) -> dict:
    """Return ``{'db_access': [...], 'file_io': [...]}`` findings for one file.

    Each finding is ``{'line', 'kind', 'snippet'}``. Comment lines and the
    interiors of triple-quoted blocks are skipped, so prose and SQL examples in
    docstrings are not mistaken for live access."""
    db_access, file_io = [], []
    # File-I/O only counts when the file also touches the catchment data tree.
    has_data_ctx = bool(_DATA_CONTEXT_RE.search(text))
    in_doc = None  # active triple-quote delimiter, or None
    for i, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()

        if in_doc:
            if in_doc in line:
                in_doc = None
            continue
        delim = next((d for d in ('"""', "'''") if stripped.startswith(d)), None)
        if delim is not None:
            if line.count(delim) % 2 == 1:
                in_doc = delim
            continue
        if stripped.startswith('#'):
            continue

        for kind, rx in _DB_RULES:
            if rx.search(line):
                db_access.append({'line': i, 'kind': kind, 'snippet': stripped[:90]})
                break  # one db-access finding per line (most specific rule wins)

        if has_data_ctx and _FILE_IO_RE.search(line):
            file_io.append({'line': i, 'kind': 'file_io', 'snippet': stripped[:90]})

    return {'db_access': db_access, 'file_io': file_io}


def scan_repo(root: Path = None) -> dict:
    """Scan the first-party tree for data access outside ``src/database``.

    Returns ``{'scanned', 'db_access_findings', 'file_io_findings',
    'file_io_files', 'allowlisted'}``. ``db_access_findings`` are the gated
    violations (the gate fails if non-empty); ``file_io_findings`` are the
    reported migration backlog (never fails the gate)."""
    root = Path(root) if root is not None else _root
    db_access, file_io, allowlisted = [], [], []
    scanned = 0
    for path in iter_source_files(root):
        try:
            text = path.read_text(encoding='utf-8')
        except (OSError, UnicodeDecodeError):
            continue
        scanned += 1
        rel = _rel(path, root)
        found = scan_text(text)
        for f in found['db_access']:
            rec = {'file': rel, **f}
            if rel in _ALLOWLIST:
                rec['reason'] = _ALLOWLIST[rel]
                allowlisted.append(rec)
            else:
                db_access.append(rec)
        for f in found['file_io']:
            file_io.append({'file': rel, **f})

    return {
        'scanned': scanned,
        'db_access_findings': db_access,
        'file_io_findings': file_io,
        'file_io_files': sorted({f['file'] for f in file_io}),
        'allowlisted': allowlisted,
    }


# ---------------------------------------------------------------------------
# Full-audit subsection (read-only render)
# ---------------------------------------------------------------------------
_KIND_LABEL = {
    'sql': 'Raw SQL statement',
    'execute': 'Cursor .execute()',
    'driver_import': 'SQL driver / ORM import',
    'connection': 'Engine / session / cursor handle',
}


def _build_data_access(styles) -> list:
    """4.4 — report data access found outside the ``src/database`` package."""
    elems = []
    elems.append(Spacer(1, 5 * mm))
    elems.append(Paragraph('4.4 Data-Access Audit', styles['h3']))
    elems.append(HRFlowable(width='100%', thickness=1, color=NAVY))
    elems.append(Spacer(1, 2 * mm))

    scan = scan_repo()
    db = scan['db_access_findings']
    n_io_files = len(scan['file_io_files'])

    gate = 'PASS' if not db else f'FAIL ({len(db)} finding(s))'
    elems.append(Paragraph(
        f'Policy: all database access goes through <b>src/database</b> '
        f'(zero-tolerance gate on SQL / ORM / driver / connection handles '
        f'outside it). Scanned <b>{scan["scanned"]}</b> files. '
        f'DB-access gate: <b>{gate}</b>.', styles['body']))
    elems.append(Spacer(1, 2 * mm))
    elems.append(Paragraph(
        f'Direct file-I/O migration backlog (tracked, non-gating): '
        f'<b>{n_io_files}</b> file(s) outside src/database still read/write the '
        f'data tree directly via json/open/glob — the un-migrated generators '
        f'(property ts/hc, stressm, book, peril, typhoon). This count shrinks as '
        f'each reader moves onto the repository seam.', styles['body']))

    if db:
        elems.append(Spacer(1, 2 * mm))
        for f in db[:40]:
            elems.append(Paragraph(
                f'• {f["file"]}:{f["line"]} — {_KIND_LABEL.get(f["kind"], f["kind"])}',
                styles['body']))
    return elems
