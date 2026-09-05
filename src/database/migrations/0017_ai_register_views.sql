-- Copyright (c) 2022-2026 MKM Research Labs. Licensed under the MIT License; see LICENSE.
-- The two AI registers, created together because they are read together: a failure mode
-- is how one system fails, a standing risk is one the firm carries across all of them,
-- and a report that shows one without the other misleads by omission.
--
-- Neither carries a mitigation status. Whether a mitigation is in place is answered from
-- documents tagged against the record, by the FINOS coverage view, and a status column
-- here would answer the same question from a different source.
CREATE TABLE IF NOT EXISTS failure_mode_register_view (
    entry_id     TEXT PRIMARY KEY,
    ai_system_id TEXT NOT NULL,
    finos_risk   TEXT NOT NULL DEFAULT '',
    data         JSONB NOT NULL,
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS failure_mode_system_idx
    ON failure_mode_register_view (ai_system_id);
-- Estate-wide: "which systems can fail this way" is the question the register answers
-- that a per-record list cannot.
CREATE INDEX IF NOT EXISTS failure_mode_risk_idx
    ON failure_mode_register_view (finos_risk);

CREATE TABLE IF NOT EXISTS standing_risk_register_view (
    risk_id      TEXT PRIMARY KEY,
    data         JSONB NOT NULL,
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

GRANT SELECT, INSERT, UPDATE, DELETE ON failure_mode_register_view TO {{app_user}};
GRANT SELECT, INSERT, UPDATE, DELETE ON standing_risk_register_view TO {{app_user}};
