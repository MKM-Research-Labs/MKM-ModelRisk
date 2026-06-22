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
"""Tests for the schema migration runner."""
from __future__ import annotations

from config import DatabaseConfig
from src.database import migration_files, owner_connection, run_migrations


def _drop_everything() -> None:
    with owner_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS events CASCADE")
            cur.execute("DROP TABLE IF EXISTS projection_checkpoints CASCADE")
            cur.execute("DROP TABLE IF EXISTS model_inventory_view CASCADE")
            cur.execute("DROP TABLE IF EXISTS mrc_meeting_view CASCADE")
            cur.execute("DROP TABLE IF EXISTS schema_migrations CASCADE")


def test_migration_files_are_ordered():
    names = [path.name for path in migration_files()]
    assert names == [
        "0001_event_store.sql",
        "0002_roles_grants.sql",
        "0003_model_inventory_view.sql",
        "0004_mrc_meeting_view.sql",
    ]


def test_run_migrations_applies_then_skips():
    _drop_everything()
    applied = run_migrations()
    assert applied == [
        "0001_event_store",
        "0002_roles_grants",
        "0003_model_inventory_view",
        "0004_mrc_meeting_view",
    ]
    # Re-running is a no-op: every version already recorded.
    assert run_migrations() == []


def test_run_migrations_accepts_explicit_config():
    # Exercises the explicit-config path of the owner connection.
    assert run_migrations(config=DatabaseConfig.from_env()) == []
