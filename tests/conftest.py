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

# Run tests against a dedicated database so they never touch dev/demo data, and
# give *every pytest process its own* database. The autouse ``_clean_event_log``
# fixture TRUNCATEs the shared ``events`` table before each test; if two pytest
# processes (two terminals, an IDE runner, xdist workers, a background agent)
# pointed at the same database, one's truncate would wipe the other's data
# mid-test. That cross-process race — not any connection pool or MVCC/cache bug —
# is what makes the suite flaky, surfacing as ConcurrencyError "expected version
# N, found 0", tamper-evidence and sign-off failures. Isolating the database per
# process makes concurrent runs impossible to corrupt (and serial runs unchanged).
_TEST_DB_BASE = (
    os.environ.get("MKM_TEST_DB_BASE")
    or os.environ.get("MKM_DB_NAME")
    or "mkm_modelrisk_test"
)
if _TEST_DB_BASE != "mkm_modelrisk":  # never shadow the dev database
    # Worker id is stable per xdist worker; PID isolates independent invocations.
    _suffix = os.environ.get("PYTEST_XDIST_WORKER") or f"p{os.getpid()}"
    # Keep a stable base so xdist workers don't double-suffix the mutated name.
    os.environ["MKM_TEST_DB_BASE"] = _TEST_DB_BASE
    os.environ["MKM_DB_NAME"] = f"{_TEST_DB_BASE}_{_suffix}"

import time  # noqa: E402

import psycopg  # noqa: E402
import pytest  # noqa: E402

from config import DatabaseConfig  # noqa: E402
from src.database import owner_connection, run_migrations  # noqa: E402


def _admin_cursor(cfg: DatabaseConfig):
    """Autocommit connection to the dev database, used to (re)create/drop the test DB."""
    return psycopg.connect(
        host=cfg.host, port=cfg.port, dbname="mkm_modelrisk",
        user=cfg.owner_user, password=cfg.owner_password, autocommit=True,
    )


def _ensure_test_database() -> None:
    cfg = DatabaseConfig.from_env()
    if cfg.name == "mkm_modelrisk":  # never auto-create the dev database
        return
    # Drop first so a database leaked by an earlier SIGKILLed run with the same
    # name starts clean. Names are unique per *live* process, so FORCE only ever
    # evicts a dead process's stragglers — never a concurrent run's connections.
    admin = _admin_cursor(cfg)
    try:
        with admin.cursor() as cur:
            cur.execute(f'DROP DATABASE IF EXISTS "{cfg.name}" WITH (FORCE)')
            cur.execute(f'CREATE DATABASE "{cfg.name}" OWNER {cfg.owner_user}')
    finally:
        admin.close()


def _drop_test_database() -> None:
    cfg = DatabaseConfig.from_env()
    if cfg.name == "mkm_modelrisk":  # never drop the dev database
        return
    admin = _admin_cursor(cfg)
    try:
        with admin.cursor() as cur:
            cur.execute(f'DROP DATABASE IF EXISTS "{cfg.name}" WITH (FORCE)')
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
    yield
    _drop_test_database()


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
            cur.execute("DELETE FROM product_view")
            cur.execute("DELETE FROM data_lineage_view")
            cur.execute("DELETE FROM ingest_receipts_view")
    yield
