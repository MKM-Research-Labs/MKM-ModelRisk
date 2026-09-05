-- Copyright (c) 2022-2026 MKM Research Labs. Licensed under the MIT License; see LICENSE.
-- Configuration snapshot read-model (rebuilt from the event log; not a source of truth).
-- Keyed by system AND version because a snapshot is one version of one system, and the
-- pair is what a diff is asked for.
CREATE TABLE IF NOT EXISTS configuration_snapshot_view (
    snapshot_id    TEXT PRIMARY KEY,
    ai_system_id   TEXT NOT NULL,
    config_version INTEGER NOT NULL,
    data           JSONB NOT NULL,
    taken_at       TEXT NOT NULL,
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS configuration_snapshot_system_idx
    ON configuration_snapshot_view (ai_system_id, config_version);

GRANT SELECT, INSERT, UPDATE, DELETE ON configuration_snapshot_view TO {{app_user}};
