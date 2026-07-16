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
