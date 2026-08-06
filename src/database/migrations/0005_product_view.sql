-- Copyright (c) 2022-2026 MKM Research Labs. Licensed under the MIT License; see LICENSE.
-- Product read-model projection (rebuilt from the event log; not a source of truth).
CREATE TABLE IF NOT EXISTS product_view (
    product_id TEXT PRIMARY KEY,
    data       JSONB NOT NULL,
    retired    BOOLEAN NOT NULL DEFAULT FALSE,
    version    INTEGER NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

GRANT SELECT, INSERT, UPDATE, DELETE ON product_view TO {{app_user}};
