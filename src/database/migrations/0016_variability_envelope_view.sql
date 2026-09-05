-- Copyright (c) 2022-2026 MKM Research Labs. Licensed under the MIT License; see LICENSE.
-- Variability envelope read-model (rebuilt from the event log; not a source of truth).
-- config_version is a column because the question asked of an envelope is almost always
-- "is this one still current", which is a comparison against the system's latest snapshot.
CREATE TABLE IF NOT EXISTS variability_envelope_view (
    envelope_id    TEXT PRIMARY KEY,
    ai_system_id   TEXT NOT NULL,
    config_version INTEGER NOT NULL,
    data           JSONB NOT NULL,
    measured_at    TEXT NOT NULL,
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS variability_envelope_system_idx
    ON variability_envelope_view (ai_system_id, config_version);

GRANT SELECT, INSERT, UPDATE, DELETE ON variability_envelope_view TO {{app_user}};
