-- Copyright (c) 2022-2026 MKM Research Labs. Licensed under the MIT License; see LICENSE.
-- Migration 0001: the event store and projection checkpoints.

-- Append-only event log. One row per recorded event. Streams are keyed by
-- (aggregate_type, aggregate_id); stream_seq is a 1-based gap-free counter and
-- the UNIQUE constraint makes two events at the same stream position impossible
-- (optimistic-concurrency backstop). event_hash chains to the previous event's
-- hash so any after-the-fact mutation is detectable.
CREATE TABLE IF NOT EXISTS events (
    global_seq     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    event_id       UUID NOT NULL DEFAULT gen_random_uuid(),
    aggregate_type TEXT NOT NULL,
    aggregate_id   TEXT NOT NULL,
    stream_seq     INTEGER NOT NULL CHECK (stream_seq > 0),
    event_type     TEXT NOT NULL,
    payload        JSONB NOT NULL DEFAULT '{}'::jsonb,
    actor          TEXT NOT NULL,
    reason         TEXT,
    recorded_at    TIMESTAMPTZ NOT NULL,
    prev_hash      TEXT,
    event_hash     TEXT NOT NULL,
    CONSTRAINT events_stream_unique UNIQUE (aggregate_type, aggregate_id, stream_seq)
);

CREATE INDEX IF NOT EXISTS events_stream_idx
    ON events (aggregate_type, aggregate_id, stream_seq);

-- Derived read models record how far they have replayed the global log.
CREATE TABLE IF NOT EXISTS projection_checkpoints (
    projection      TEXT PRIMARY KEY,
    last_global_seq BIGINT NOT NULL DEFAULT 0,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
