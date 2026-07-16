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
            host=os.environ.get("MKM_DB_HOST", _DEFAULTS["host"]),
            port=int(os.environ.get("MKM_DB_PORT", _DEFAULTS["port"])),
            name=os.environ.get("MKM_DB_NAME", _DEFAULTS["name"]),
            owner_user=os.environ.get("MKM_DB_OWNER_USER", _DEFAULTS["owner_user"]),
            owner_password=os.environ.get(
                "MKM_DB_OWNER_PASSWORD", _DEFAULTS["owner_password"]
            ),
            app_user=os.environ.get("MKM_DB_APP_USER", _DEFAULTS["app_user"]),
            app_password=os.environ.get(
                "MKM_DB_APP_PASSWORD", _DEFAULTS["app_password"]
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
