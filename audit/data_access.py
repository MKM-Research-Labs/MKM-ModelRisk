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
"""Data-access audit (coding rule R6): the store is reached only via one package.

Policy: **all database access goes through** ``src/database`` — no raw SQL, ORM
sessions, DB-driver imports, or connection/cursor handles anywhere else. Every
other module obtains data through that package's public API. This automates
what was previously an R6 hand-review.

A finding is a SQL keyword (``SELECT … FROM``, ``INSERT INTO``, ``UPDATE … SET``,
``DELETE FROM``, ``CREATE/ALTER/DROP TABLE``…), a ``.execute(`` / ``.executemany(``
call, a ``sqlalchemy`` / ``psycopg`` / ``asyncpg`` / ``sqlite3`` import, or a
connection handle (``create_engine``, ``sessionmaker``, ``.cursor(``) found
**outside** ``src/database``. Comment lines and triple-quoted blocks are skipped
so prose and SQL examples in docstrings are not mistaken for live access.

Reported rather than gated for now (the read-model projections still execute SQL
directly). Registered exceptions live in ``_ALLOWLIST``; drive the count to zero
to promote it to a hard gate.
"""
from __future__ import annotations

import re

from config.audit import DATABASE_PACKAGE, REPO_SCAN_DIRS

from audit._walk import code_files, rel

_SELF_PKG = "audit/"

# First-party files exempt by explicit, justified registration. Kept minimal.
_ALLOWLIST: dict[str, str] = {
    # (none yet)
}

# Real SQL statements (structural, so prose like "update the set of …" or an
# identifier like ``delete_from_cache`` cannot match).
_SQL_RE = re.compile(
    r"\bSELECT\b[\s\S]*?\bFROM\b"
    r"|\bINSERT\s+INTO\b"
    r"|\bUPDATE\b[\s\S]*?\bSET\b[\s\S]*?="   # SET <col> = … — an assignment, not prose
    r"|\bDELETE\s+FROM\b"
    r"|\bCREATE\s+(?:TABLE|INDEX|SCHEMA|VIEW)\b"
    r"|\bALTER\s+TABLE\b"
    r"|\bDROP\s+(?:TABLE|INDEX|VIEW)\b",
    re.IGNORECASE,
)
_EXEC_RE = re.compile(r"\.execute(?:many|script)?\s*\(")
_DRIVER_IMPORT_RE = re.compile(
    r"^\s*(?:import|from)\s+(?:sqlalchemy|psycopg2?|asyncpg|sqlite3|aiomysql|pymysql|MySQLdb)\b"
)
_CONN_RE = re.compile(r"\b(?:create_engine|sessionmaker|scoped_session)\s*\(|\.cursor\s*\(")

_RULES = (
    ("sql", _SQL_RE),
    ("execute", _EXEC_RE),
    ("driver_import", _DRIVER_IMPORT_RE),
    ("connection", _CONN_RE),
)


def _scan_text(text: str, path: str) -> list[dict]:
    """Data-access findings for one file's *text* (comments/docstrings skipped)."""
    out = []
    in_doc = None  # active triple-quote delimiter, or None
    for index, line in enumerate(text.splitlines(), start=1):
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
        if stripped.startswith("#"):
            continue
        for kind, rx in _RULES:
            if rx.search(line):
                out.append({"path": path, "line": index, "kind": kind,
                            "snippet": stripped[:90]})
                break  # one finding per line (most specific rule wins)
    return out


def data_access_findings() -> list[dict]:
    """Report data access found outside the sanctioned ``src/database`` package.

    Skips the sanctioned package, this audit package (its source contains the
    very patterns it searches for) and allowlisted files.
    """
    exempt = (DATABASE_PACKAGE + "/", _SELF_PKG)
    findings = []
    for path in code_files(REPO_SCAN_DIRS, (".py",)):
        relpath = rel(path)
        if relpath.startswith(exempt) or relpath in _ALLOWLIST:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        findings.extend(_scan_text(text, relpath))
    return sorted(findings, key=lambda f: (f["path"], f["line"]))
