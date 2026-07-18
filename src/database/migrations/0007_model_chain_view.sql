-- Copyright (c) 2022-2026 MKM Research Labs. Licensed under the MIT License; see LICENSE.
-- Migration 0007: model-chain read model (migration Phase 2 — Model Chain).
--
-- A derived, fully rebuildable projection of the latest 'string of pearls'
-- dependency graph per producing repo. A projection, not a source of truth, so
-- the app role may freely mutate it; the authoritative history is the event log.

-- Latest model chain per producing repo (aggregate ModelChain).
CREATE TABLE IF NOT EXISTS model_chain_view (
    source_repo  TEXT PRIMARY KEY,
    data         JSONB NOT NULL,
    content_hash TEXT NOT NULL,
    version      INTEGER NOT NULL,
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

GRANT SELECT, INSERT, UPDATE, DELETE ON model_chain_view TO mkm_app;
