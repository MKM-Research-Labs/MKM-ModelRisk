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
"""Tests for the schema migration runner."""
from __future__ import annotations

from dataclasses import replace

import pytest

from config import DatabaseConfig
from src.database import migration_files, owner_connection, run_migrations
from src.database._migrate import render

ROLES_SQL = next(p for p in migration_files() if p.stem == "0002_roles_grants")


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
        "0005_product_view.sql",
        "0006_ingest_views.sql",
        "0007_model_chain_view.sql",
        "0008_model_handoff_view.sql",
        "0009_field_lineage_view.sql",
        "0010_client_view.sql",
        "0011_ml_application_view.sql",
    ]


def test_run_migrations_applies_then_skips():
    _drop_everything()
    applied = run_migrations()
    assert applied == [
        "0001_event_store",
        "0002_roles_grants",
        "0003_model_inventory_view",
        "0004_mrc_meeting_view",
        "0005_product_view",
        "0006_ingest_views",
        "0007_model_chain_view",
        "0008_model_handoff_view",
        "0009_field_lineage_view",
        "0010_client_view",
        "0011_ml_application_view",
    ]
    # Re-running is a no-op: every version already recorded.
    assert run_migrations() == []


def test_run_migrations_accepts_explicit_config():
    # Exercises the explicit-config path of the owner connection.
    assert run_migrations(config=DatabaseConfig.from_env()) == []


def _config(**overrides) -> DatabaseConfig:
    return replace(DatabaseConfig.from_env(), **overrides)


def test_render_grants_to_the_configured_runtime_role():
    """A deployment that renames the runtime role gets its grants written against
    that role — otherwise DB_APP_USER would connect as a role holding none."""
    sql = render(ROLES_SQL.read_text(), _config(app_user="moody_app", app_password="s3cret"))
    assert "GRANT USAGE ON SCHEMA public TO moody_app;" in sql
    assert "CREATE ROLE moody_app LOGIN PASSWORD 's3cret'" in sql
    assert "{{app_user}}" not in sql and "{{app_password}}" not in sql


def test_render_escapes_a_quote_in_the_password():
    sql = render(ROLES_SQL.read_text(), _config(app_password="pa'ss"))
    assert "LOGIN PASSWORD 'pa''ss'" in sql


def test_render_refuses_a_role_name_that_is_not_an_identifier():
    """The role goes in as a bare identifier (no parameter can carry one), so a
    name carrying SQL is refused before it reaches a statement."""
    with pytest.raises(ValueError):
        render(ROLES_SQL.read_text(), _config(app_user="app; DROP TABLE events"))
