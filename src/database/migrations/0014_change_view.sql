-- Copyright (c) 2022-2026 MKM Research Labs. Licensed under the MIT License; see LICENSE.
-- Change register read-model projection (rebuilt from the event log; not a source of truth).
-- subject_type/subject_id are columns rather than JSONB keys because every read this
-- table serves is "what is outstanding against this record".
CREATE TABLE IF NOT EXISTS change_view (
    change_id    TEXT PRIMARY KEY,
    data         JSONB NOT NULL,
    subject_type TEXT NOT NULL,
    subject_id   TEXT NOT NULL,
    superseded   BOOLEAN NOT NULL DEFAULT FALSE,
    version      INTEGER NOT NULL,
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS change_view_subject_idx ON change_view (subject_type, subject_id);

GRANT SELECT, INSERT, UPDATE, DELETE ON change_view TO {{app_user}};
