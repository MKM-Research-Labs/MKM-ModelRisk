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
"""Schema migration runner.

Applies numbered ``*.sql`` files in lexical order as the owner role, recording
each in ``schema_migrations`` so re-running is a no-op. Plain SQL migrations are
deliberately transparent and reviewable — a good fit for a regulated product.
"""
from __future__ import annotations

from pathlib import Path

from config.paths import MIGRATIONS_DIR as _MIGRATIONS_DIR
from src.database._connection import owner_connection


def migration_files() -> list[Path]:
    """All migration SQL files in apply order."""
    return sorted(_MIGRATIONS_DIR.glob("*.sql"))


def _ensure_table(cur) -> None:
    cur.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations ("
        " version TEXT PRIMARY KEY,"
        " applied_at TIMESTAMPTZ NOT NULL DEFAULT now())"
    )


def _applied_versions(cur) -> set[str]:
    cur.execute("SELECT version FROM schema_migrations")
    return {row[0] for row in cur.fetchall()}


def run_migrations(config=None) -> list[str]:
    """Apply any pending migrations; return the versions newly applied."""
    newly_applied: list[str] = []
    with owner_connection(config) as conn:
        with conn.cursor() as cur:
            _ensure_table(cur)
            done = _applied_versions(cur)
            for path in migration_files():
                version = path.stem
                if version in done:
                    continue
                cur.execute(path.read_text())
                cur.execute(
                    "INSERT INTO schema_migrations (version) VALUES (%s)",
                    (version,),
                )
                newly_applied.append(version)
    return newly_applied
