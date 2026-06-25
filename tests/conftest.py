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
"""Shared test fixtures: ensure the schema is migrated and reset the log."""
from __future__ import annotations

import os

# Run tests against a dedicated database so they never touch dev/demo data.
os.environ.setdefault("MKM_DB_NAME", "mkm_modelrisk_test")

import time  # noqa: E402

import psycopg  # noqa: E402
import pytest  # noqa: E402

from config import DatabaseConfig  # noqa: E402
from src.database import owner_connection, run_migrations  # noqa: E402


def _ensure_test_database() -> None:
    cfg = DatabaseConfig.from_env()
    if cfg.name == "mkm_modelrisk":  # never auto-create the dev database
        return
    admin = psycopg.connect(
        host=cfg.host, port=cfg.port, dbname="mkm_modelrisk",
        user=cfg.owner_user, password=cfg.owner_password, autocommit=True,
    )
    try:
        with admin.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (cfg.name,))
            if cur.fetchone() is None:
                cur.execute(f'CREATE DATABASE "{cfg.name}" OWNER {cfg.owner_user}')
    finally:
        admin.close()


def _wait_for_db(attempts: int = 30, delay: float = 1.0) -> None:
    last: Exception | None = None
    for _ in range(attempts):
        try:
            with owner_connection() as conn:
                conn.execute("SELECT 1")
            return
        except psycopg.OperationalError as exc:
            last = exc
            time.sleep(delay)
    raise RuntimeError(f"PostgreSQL not reachable on the configured port: {last}")


@pytest.fixture(scope="session", autouse=True)
def _database_ready():
    _ensure_test_database()
    _wait_for_db()
    run_migrations()


@pytest.fixture(autouse=True)
def _isolate_uploads(tmp_path, monkeypatch):
    # Keep uploaded test files out of the real uploads directory.
    monkeypatch.setattr("src.files.store.UPLOAD_DIR", tmp_path / "uploads")


@pytest.fixture(autouse=True)
def _clean_event_log():
    # Reset as the owner role; the app role is forbidden from truncating.
    with owner_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE events RESTART IDENTITY")
            cur.execute("UPDATE projection_checkpoints SET last_global_seq = 0")
            cur.execute("DELETE FROM model_inventory_view")
            cur.execute("DELETE FROM mrc_meeting_view")
            cur.execute("DELETE FROM pvm_view")
    yield
