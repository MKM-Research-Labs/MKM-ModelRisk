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
"""Database connection parameters.

The single home for database configuration (coding rule R1). Values are read
from the environment with sensible defaults (matching ``scripts/pg.sh``) so a
local native PostgreSQL cluster and the tests work out of the box.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

# A database that already exists, connected to only while creating another (you
# cannot connect to the database you are about to CREATE). ``postgres`` is the
# cluster's standard bookkeeping database, present in every cluster initdb makes;
# naming a product database here would strand any install that does not have it.
MAINTENANCE_DB = os.environ.get("DB_MAINTENANCE_NAME", "postgres")

_DEFAULTS = {
    "host": "localhost",
    "port": "5433",
    "name": "mkm_modelrisk",
    "owner_user": "mkm_owner",
    "owner_password": "mkm_dev_pw",
    "app_user": "mkm_app",
    "app_password": "mkm_app_dev_pw",
}


@dataclass(frozen=True)
class DatabaseConfig:
    """Connection settings for the owner (migrations) and app (runtime) roles."""

    host: str
    port: int
    name: str
    owner_user: str
    owner_password: str
    app_user: str
    app_password: str

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        return cls(
            host=os.environ.get("DB_HOST", _DEFAULTS["host"]),
            port=int(os.environ.get("DB_PORT", _DEFAULTS["port"])),
            name=os.environ.get("DB_NAME", _DEFAULTS["name"]),
            owner_user=os.environ.get("DB_OWNER_USER", _DEFAULTS["owner_user"]),
            owner_password=os.environ.get(
                "DB_OWNER_PASSWORD", _DEFAULTS["owner_password"]
            ),
            app_user=os.environ.get("DB_APP_USER", _DEFAULTS["app_user"]),
            app_password=os.environ.get(
                "DB_APP_PASSWORD", _DEFAULTS["app_password"]
            ),
        )

    def _conninfo(self, user: str, password: str) -> dict:
        return {
            "host": self.host,
            "port": self.port,
            "dbname": self.name,
            "user": user,
            "password": password,
        }

    def app_conninfo(self) -> dict:
        """Connection kwargs for the runtime application role."""
        return self._conninfo(self.app_user, self.app_password)

    def owner_conninfo(self) -> dict:
        """Connection kwargs for the schema-owner role (migrations, tests)."""
        return self._conninfo(self.owner_user, self.owner_password)


# Tokens the migration runner substitutes before executing a migration, so the
# runtime role the grants are written against is the one the deployment actually
# connects as (DB_APP_USER). Written into the SQL as a literal name instead, a
# deployment that renamed the role would connect as a role holding no grants —
# the environment variable would be a promise the schema does not keep.
MIGRATION_APP_USER_TOKEN = "{{app_user}}"
MIGRATION_APP_PASSWORD_TOKEN = "{{app_password}}"

# A role name is substituted into SQL as a bare identifier (a parameter cannot
# carry one), so it must look like one before it goes anywhere near a statement.
ROLE_NAME_PATTERN = r"[A-Za-z_][A-Za-z0-9_]*"

# Key for the PostgreSQL advisory lock the migration runner holds while it works,
# so that only one process migrates a given database at a time. It matters now
# that the console is served by several gunicorn workers: without it, two
# processes starting together both read the same migration as pending, both
# execute its DDL, and the loser dies on the schema_migrations primary key — a
# worker that crashes on boot with nothing to explain it. The value is arbitrary
# but must be stable and unshared; advisory locks live in one cluster-wide space.
MIGRATION_LOCK_KEY = 4113220106


# Databases that hold real, non-disposable data. The test suite's teardown
# fixtures TRUNCATE the event log between tests; pointed at one of these they
# would wipe the live estate — which is exactly how the demo log was lost once
# (a `pytest` run with a dev `.env` present resolved DB_NAME to the live
# database). ``assert_disposable`` is the single guard every destructive fixture
# calls, so neither a stray test run nor a future fixture can reset a real DB.
PROTECTED_DB_NAMES = frozenset({"mkm_modelrisk", "mkm_modelrisk_demo"})


def assert_disposable(name: str) -> None:
    """Raise unless ``name`` is a throwaway test database.

    Guards every ``TRUNCATE``/``DROP`` in the test fixtures. The message tells
    the caller how to get onto a scratch database rather than merely failing.
    """
    if name in PROTECTED_DB_NAMES:
        raise RuntimeError(
            f"Refusing to run destructive test fixtures against {name!r}: it is a "
            "protected database holding real data. Tests must use a scratch "
            "database — unset DB_NAME (the suite then derives 'mkm_modelrisk_test'), "
            "or set TEST_DB_BASE to a dedicated *_test name. See tests/conftest.py."
        )
