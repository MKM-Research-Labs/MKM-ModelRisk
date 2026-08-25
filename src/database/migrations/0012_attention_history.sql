-- Copyright (c) 2022-2026 MKM Research Labs. Licensed under the MIT License; see LICENSE.
--
-- Finding history and the dashboard's trend series.
--
-- NOT named *_view, and the difference is the point. Every other table here is a
-- read model replayed from the event log, so losing one costs a rebuild. These two
-- are OBSERVATIONS: what the completeness audit found on a given day. Nothing in
-- the event log records that, because nobody decided it -- it is what the register
-- happened to say when it was looked at.
--
-- They are in principle reconstructible: the log holds the full history of the
-- register, so the audit could be re-run against a replayed past state. That is
-- expensive and not implemented, so treat these as state worth backing up rather
-- than as state that can be regenerated on demand.
--
-- Neither is a governance record. Losing them loses the trend line and the ability
-- to age a finding; it loses nothing a committee decided.

-- One row per finding ever observed, keyed on what identifies it across days:
-- the record it is against and the thing that is missing.
CREATE TABLE IF NOT EXISTS finding_history (
    finding_key TEXT PRIMARY KEY,
    data        JSONB NOT NULL,
    first_seen  DATE NOT NULL,
    last_seen   DATE NOT NULL,
    closed_at   DATE
);

-- One row per day observed: the estate-wide totals the strategic view reads.
CREATE TABLE IF NOT EXISTS attention_trend (
    as_of DATE PRIMARY KEY,
    data  JSONB NOT NULL
);

GRANT SELECT, INSERT, UPDATE, DELETE ON finding_history TO {{app_user}};
GRANT SELECT, INSERT, UPDATE, DELETE ON attention_trend TO {{app_user}};
