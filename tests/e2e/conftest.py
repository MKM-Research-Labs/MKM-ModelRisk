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
"""End-to-end harness: a live Flask subprocess on an isolated ``mkm_modelrisk_e2e`` DB.

The browser tests here are marked ``e2e`` and excluded from the default ``pytest``
run. Drive them with ``pytest tests/e2e -m e2e``.
"""
from __future__ import annotations

import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import psycopg
import pytest

from config import DatabaseConfig

try:
    import playwright  # noqa: F401
except ImportError:
    collect_ignore_glob = ["test_e2e_*.py"]

E2E_DB = "mkm_modelrisk_e2e"
REPO_ROOT = Path(__file__).resolve().parents[2]


def _admin_conn(cfg: DatabaseConfig, dbname: str):
    return psycopg.connect(
        host=cfg.host, port=cfg.port, dbname=dbname,
        user=cfg.owner_user, password=cfg.owner_password, autocommit=True,
    )


def _ensure_db(cfg: DatabaseConfig) -> None:
    with _admin_conn(cfg, "mkm_modelrisk") as admin, admin.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (E2E_DB,))
        if cur.fetchone() is None:
            cur.execute(f'CREATE DATABASE "{E2E_DB}" OWNER {cfg.owner_user}')


def _free_port() -> int:
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def _wait_until_ready(url: str, proc: subprocess.Popen, log: Path, attempts: int = 80) -> None:
    for _ in range(attempts):
        if proc.poll() is not None:
            raise RuntimeError("e2e server exited early:\n" + log.read_text(errors="replace"))
        try:
            with urllib.request.urlopen(url, timeout=1) as resp:
                if resp.status == 200:
                    return
        except (urllib.error.URLError, ConnectionError, OSError):
            time.sleep(0.5)
    raise RuntimeError("e2e server never became ready:\n" + log.read_text(errors="replace"))


@pytest.fixture(scope="session")
def live_server(tmp_path_factory) -> str:
    cfg = DatabaseConfig.from_env()
    _ensure_db(cfg)
    port = _free_port()
    workdir = tmp_path_factory.mktemp("e2e")
    log = workdir / "server.log"
    env = {
        "MKM_DB_NAME": E2E_DB,
        "MKM_WEB_HOST": "127.0.0.1",
        "MKM_WEB_PORT": str(port),
        "MKM_UPLOAD_DIR": str(workdir / "uploads"),
        "PYTHONPATH": str(REPO_ROOT),
        "PATH": __import__("os").environ.get("PATH", ""),
    }
    with log.open("wb") as handle:
        proc = subprocess.Popen(
            [sys.executable, str(REPO_ROOT / "tests" / "e2e" / "_runserver.py")],
            cwd=str(REPO_ROOT), env=env, stdout=handle, stderr=subprocess.STDOUT,
        )
        url = f"http://127.0.0.1:{port}"
        try:
            _wait_until_ready(url, proc, log)
            yield url
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()


@pytest.fixture(scope="session")
def base_url(live_server: str) -> str:
    return live_server


@pytest.fixture(autouse=True)
def _reset_e2e(live_server):
    """Truncate the event log and projections before each test (owner role)."""
    cfg = DatabaseConfig.from_env()
    with _admin_conn(cfg, E2E_DB) as conn, conn.cursor() as cur:
        cur.execute("TRUNCATE events RESTART IDENTITY")
        cur.execute("UPDATE projection_checkpoints SET last_global_seq = 0")
        cur.execute("DELETE FROM model_inventory_view")
        cur.execute("DELETE FROM mrc_meeting_view")
        cur.execute("DELETE FROM product_view")
    yield
