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
"""Tests for the sanctioned CREATE DATABASE admin helper (rule R6)."""
from __future__ import annotations

import psycopg

from config import DatabaseConfig
from src.database import create_database

_PROBE = "mkm_modelrisk_r6_probe"


def _drop_probe() -> None:
    cfg = DatabaseConfig.from_env()
    with psycopg.connect(
        host=cfg.host, port=cfg.port, dbname="mkm_modelrisk",
        user=cfg.owner_user, password=cfg.owner_password, autocommit=True,
    ) as admin:
        with admin.cursor() as cur:
            cur.execute(f'DROP DATABASE IF EXISTS "{_PROBE}" WITH (FORCE)')


def test_create_database_creates_then_reports_existing():
    _drop_probe()
    try:
        assert create_database(_PROBE) is True      # first call creates it
        assert create_database(_PROBE) is False     # second call: already exists
    finally:
        _drop_probe()
