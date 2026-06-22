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
"""Database connection parameters.

The single home for database configuration (coding rule R1). Values are read
from the environment with defaults matching ``docker-compose.yml`` so local
development and tests work out of the box.
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
