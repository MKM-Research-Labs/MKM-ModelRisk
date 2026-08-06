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
"""Low-level database connections.

The only module that opens connections to PostgreSQL. Everything else in the
codebase reaches the database through ``src.database`` (coding rule R6).
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

import psycopg
from psycopg import sql

from config import DatabaseConfig
from config.database import MAINTENANCE_DB as _MAINTENANCE_DB


def create_database(name: str, *, config: DatabaseConfig | None = None) -> bool:
    """Create database ``name`` if it does not already exist, as the owner role
    over an autocommit connection to the maintenance database. Returns ``True``
    if it was created, ``False`` if it already existed.

    The single sanctioned home for the ``CREATE DATABASE`` admin operation (R6),
    so callers (e.g. the demo bootstrap) never open their own driver connection.
    """
    cfg = config or DatabaseConfig.from_env()
    with psycopg.connect(
        host=cfg.host, port=cfg.port, dbname=_MAINTENANCE_DB,
        user=cfg.owner_user, password=cfg.owner_password, autocommit=True,
    ) as admin:
        with admin.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (name,))
            if cur.fetchone() is not None:
                return False
            cur.execute(sql.SQL("CREATE DATABASE {name} OWNER {owner}").format(
                name=sql.Identifier(name), owner=sql.Identifier(cfg.owner_user)))
    return True


@contextmanager
def app_connection(
    config: DatabaseConfig | None = None,
) -> Iterator[psycopg.Connection]:
    """Open a connection as the runtime application role (append/read only)."""
    cfg = config or DatabaseConfig.from_env()
    with psycopg.connect(**cfg.app_conninfo()) as conn:
        yield conn


@contextmanager
def owner_connection(
    config: DatabaseConfig | None = None,
) -> Iterator[psycopg.Connection]:
    """Open a connection as the schema-owner role (migrations, test resets)."""
    cfg = config or DatabaseConfig.from_env()
    with psycopg.connect(**cfg.owner_conninfo()) as conn:
        yield conn
