-- Copyright (c) 2022-2026 MKM Research Labs. Licensed under the MIT License; see LICENSE.
-- Migration 0008: model-handoff read model (migration Phase B — Handoffs).
--
-- A derived, fully rebuildable projection of each declared model-to-model
-- handoff: the field lineage crossing the edge plus the compatibility analysis
-- the MRC reviews. A projection, not a source of truth — the authoritative
-- history is the event log; the app role may freely mutate this table.

-- One row per declared chain edge (aggregate ModelHandoff, id "from~to").
CREATE TABLE IF NOT EXISTS model_handoff_view (
    handoff_id TEXT PRIMARY KEY,
    data       JSONB NOT NULL,
    version    INTEGER NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

GRANT SELECT, INSERT, UPDATE, DELETE ON model_handoff_view TO mkm_app;
