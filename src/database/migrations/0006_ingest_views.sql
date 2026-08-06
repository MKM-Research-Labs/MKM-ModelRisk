-- Copyright (c) 2022-2026 MKM Research Labs. Licensed under the MIT License; see LICENSE.
-- Migration 0006: ingest read models (Phase 0 collector foundation).
--
-- Two derived, fully rebuildable projections for the ingest spine. Both are
-- projections (not sources of truth), so the app role may freely mutate them;
-- the authoritative history remains the append-only event log.

-- Latest data-lineage manifest per producing repo (aggregate DataLineageManifest).
CREATE TABLE IF NOT EXISTS data_lineage_view (
    source_repo  TEXT PRIMARY KEY,
    data         JSONB NOT NULL,
    content_hash TEXT NOT NULL,
    version      INTEGER NOT NULL,
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

GRANT SELECT, INSERT, UPDATE, DELETE ON data_lineage_view TO {{app_user}};

-- Last accepted ingestion per (artifact, source_repo) (aggregate IngestReceipt).
CREATE TABLE IF NOT EXISTS ingest_receipts_view (
    receipt_id   TEXT PRIMARY KEY,
    data         JSONB NOT NULL,
    artifact     TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    version      INTEGER NOT NULL,
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

GRANT SELECT, INSERT, UPDATE, DELETE ON ingest_receipts_view TO {{app_user}};
