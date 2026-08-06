-- Copyright (c) 2022-2026 MKM Research Labs. Licensed under the MIT License; see LICENSE.
-- Migration 0004: MRC-meeting read model (projection).
--
-- A derived, fully rebuildable current-state view of the MRC-meeting aggregate.
-- The nested agenda/decisions/actions collections live in the JSONB document;
-- status is denormalised to its own column for listing and filtering.
CREATE TABLE IF NOT EXISTS mrc_meeting_view (
    meeting_id TEXT PRIMARY KEY,
    data       JSONB NOT NULL,
    status     TEXT,
    version    INTEGER NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

GRANT SELECT, INSERT, UPDATE, DELETE ON mrc_meeting_view TO {{app_user}};
