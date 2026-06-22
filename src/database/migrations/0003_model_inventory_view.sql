-- Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
-- Migration 0003: model-inventory read model (projection).
--
-- A derived, fully rebuildable current-state view of the model-inventory
-- aggregate. Because it is a projection (not a source of truth) the app role
-- may freely mutate it; the authoritative history remains the append-only log.
CREATE TABLE IF NOT EXISTS model_inventory_view (
    model_id   TEXT PRIMARY KEY,
    data       JSONB NOT NULL,
    retired    BOOLEAN NOT NULL DEFAULT FALSE,
    version    INTEGER NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

GRANT SELECT, INSERT, UPDATE, DELETE ON model_inventory_view TO mkm_app;
