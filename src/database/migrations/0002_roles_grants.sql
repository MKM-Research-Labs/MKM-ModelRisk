-- Copyright (c) 2022-2026 MKM Research Labs. Licensed under the MIT License; see LICENSE.
-- Migration 0002: the runtime application role and its grants.
--
-- Immutability is enforced here, at the database-grant level: the application
-- role may append to and read the event log, but UPDATE/DELETE/TRUNCATE are
-- revoked. Projections are derived and rebuildable, so the app may mutate them.
--
-- The role name and password are filled in by the migration runner from the
-- deployment's DB_APP_USER / DB_APP_PASSWORD, so the grants below are written
-- against the role the application actually connects as. Locally that is the
-- development pair in .env.example; in a deployed environment the client
-- provisions this role and its secret.

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '{{app_user}}') THEN
        CREATE ROLE {{app_user}} LOGIN PASSWORD '{{app_password}}';
    END IF;
END
$$;

GRANT USAGE ON SCHEMA public TO {{app_user}};

-- Event log: append + read only. No mutation, ever.
GRANT SELECT, INSERT ON events TO {{app_user}};
REVOKE UPDATE, DELETE, TRUNCATE ON events FROM {{app_user}};

-- Projections (derived, rebuildable) may be mutated by the app.
GRANT SELECT, INSERT, UPDATE, DELETE ON projection_checkpoints TO {{app_user}};
