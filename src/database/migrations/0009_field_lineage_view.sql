-- Copyright (c) 2022-2026 MKM Research Labs. Licensed under the MIT License; see LICENSE.
-- Migration 0009: field-lineage read model (migration — BCBS 239 Principle 3).
--
-- A derived, fully rebuildable projection of the latest report -> section -> field
-- lineage catalogue pushed by each producing repo: where every field on every
-- report gets its value from. A projection, not a source of truth — the
-- authoritative history is the event log; the app role may freely mutate this table.

-- One row per producing repo (aggregate FieldLineageRegistry, id = source_repo).
CREATE TABLE IF NOT EXISTS field_lineage_view (
    source_repo  TEXT PRIMARY KEY,
    data         JSONB NOT NULL,
    content_hash TEXT NOT NULL,
    version      INTEGER NOT NULL,
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

GRANT SELECT, INSERT, UPDATE, DELETE ON field_lineage_view TO mkm_app;
