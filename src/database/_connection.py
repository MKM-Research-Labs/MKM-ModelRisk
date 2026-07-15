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

# A pre-existing database to connect to while creating another (you cannot
# connect to the database you are about to CREATE).
_MAINTENANCE_DB = "mkm_modelrisk"


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
