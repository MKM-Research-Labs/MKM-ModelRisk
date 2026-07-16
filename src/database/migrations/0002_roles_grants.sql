-- Copyright (c) 2022-2026 MKM Research Labs. Licensed under the MIT License; see LICENSE.
-- Migration 0002: the runtime application role and its grants.
--
-- Immutability is enforced here, at the database-grant level: the application
-- role may append to and read the event log, but UPDATE/DELETE/TRUNCATE are
-- revoked. Projections are derived and rebuildable, so the app may mutate them.
--
-- NOTE: the password below is for LOCAL DEVELOPMENT ONLY (matches .env.example).
-- In a deployed environment the client provisions this role and its secret.

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'mkm_app') THEN
        CREATE ROLE mkm_app LOGIN PASSWORD 'mkm_app_dev_pw';
    END IF;
END
$$;

GRANT USAGE ON SCHEMA public TO mkm_app;

-- Event log: append + read only. No mutation, ever.
GRANT SELECT, INSERT ON events TO mkm_app;
REVOKE UPDATE, DELETE, TRUNCATE ON events FROM mkm_app;

-- Projections (derived, rebuildable) may be mutated by the app.
GRANT SELECT, INSERT, UPDATE, DELETE ON projection_checkpoints TO mkm_app;
