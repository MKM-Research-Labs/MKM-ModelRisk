# Enforcing event-log immutability on SQL Server

The platform's central claim is that the event log is the system of record and
cannot be rewritten. On PostgreSQL that is not a convention — it is enforced by the
database, in `src/database/migrations/0002_roles_grants.sql`:

```sql
GRANT SELECT, INSERT ON events TO {{app_user}};
REVOKE UPDATE, DELETE, TRUNCATE ON events FROM {{app_user}};
```

A deployment on **Microsoft SQL Server** does not inherit that. The driver swap
moves the queries; it does not move the grants, which are DDL the PostgreSQL
migration applies. Until the equivalent is in place, the runtime account can
rewrite the log — the hash chain will still *detect* it, but nothing *prevents* it,
and "enforced at the database-grant level" is a claim you may be making to an
assessor.

> **Do not add this file's SQL to `src/database/migrations/`.** The runner globs
> `*.sql` and applies **every** file in lexical order as PostgreSQL — a T-SQL file
> dropped in there would be executed against Postgres and fail the migration.

---

## The one thing that differs from PostgreSQL: `DENY`, not `REVOKE`

On SQL Server, `REVOKE` only removes a permission that was granted **directly**. It
does **not** override a permission inherited through role membership. If the
application user is a member of `db_datawriter` — a very common way to set up an
app account — then `REVOKE UPDATE ON events` changes nothing at all, and the log
stays writable.

`DENY` is the one that wins: it overrides every grant, direct or inherited.

Two smaller differences:

- **There is no `TRUNCATE` permission.** `TRUNCATE TABLE` is authorised by `ALTER`
  on the table, so blocking it means `DENY ALTER`.
- **`sysadmin` bypasses permission checks entirely**, and `db_owner` will generally
  defeat this too. If the app connects as either, no `DENY` will save you — check
  that first (below).

## Apply it

Run against the application database, as an administrator. Idempotent: safe to
re-run. Replace the identifiers if the deployment renamed them.

```sql
-- 1. The runtime principal (skip whichever half already exists).
IF NOT EXISTS (SELECT 1 FROM sys.server_principals WHERE name = N'mkm_app')
    CREATE LOGIN [mkm_app] WITH PASSWORD = N'<the deployment secret>';
GO
IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = N'mkm_app')
    CREATE USER [mkm_app] FOR LOGIN [mkm_app];
GO

-- 2. The event log: append and read, nothing else. DENY (not REVOKE) so that
--    membership of db_datawriter or similar cannot grant it back.
GRANT SELECT, INSERT ON dbo.events TO [mkm_app];
DENY UPDATE, DELETE ON dbo.events TO [mkm_app];
DENY ALTER ON dbo.events TO [mkm_app];          -- TRUNCATE is authorised by ALTER
GO

-- 3. Projections are derived and rebuildable, so the app may mutate them --
--    exactly as on PostgreSQL.
GRANT SELECT, INSERT, UPDATE, DELETE ON dbo.projection_checkpoints TO [mkm_app];
GRANT SELECT, INSERT, UPDATE, DELETE ON dbo.client_view          TO [mkm_app];
GRANT SELECT, INSERT, UPDATE, DELETE ON dbo.data_lineage_view    TO [mkm_app];
GRANT SELECT, INSERT, UPDATE, DELETE ON dbo.field_lineage_view   TO [mkm_app];
GRANT SELECT, INSERT, UPDATE, DELETE ON dbo.ingest_receipts_view TO [mkm_app];
GRANT SELECT, INSERT, UPDATE, DELETE ON dbo.model_chain_view     TO [mkm_app];
GRANT SELECT, INSERT, UPDATE, DELETE ON dbo.model_handoff_view   TO [mkm_app];
GRANT SELECT, INSERT, UPDATE, DELETE ON dbo.model_inventory_view TO [mkm_app];
GRANT SELECT, INSERT, UPDATE, DELETE ON dbo.mrc_meeting_view     TO [mkm_app];
GRANT SELECT, INSERT, UPDATE, DELETE ON dbo.product_view         TO [mkm_app];
GO
```

## Prove it took effect

Permissions that look right in a script and permissions that are actually in force
are different things. Both checks are worth keeping as evidence.

**1. The account is not privileged enough to ignore the DENY.** Both must return
`0`; anything else means the `DENY` above is decorative.

```sql
SELECT IS_SRVROLEMEMBER('sysadmin', 'mkm_app') AS is_sysadmin;
EXECUTE AS USER = N'mkm_app';
SELECT IS_ROLEMEMBER('db_owner') AS is_db_owner;
REVERT;
```

**2. The permissions are recorded as expected** — `SELECT`/`INSERT` granted,
`UPDATE`/`DELETE`/`ALTER` denied:

```sql
SELECT p.permission_name, p.state_desc
FROM   sys.database_permissions p
JOIN   sys.objects o            ON o.object_id = p.major_id
JOIN   sys.database_principals pr ON pr.principal_id = p.grantee_principal_id
WHERE  pr.name = N'mkm_app' AND o.name = N'events'
ORDER  BY p.permission_name;
```

**3. It actually blocks a write.** The functional test, which is the only one an
assessor should accept. `WHERE 1 = 0` matches no rows — SQL Server checks the
permission on the object regardless, so this cannot alter data even if the `DENY`
were missing.

```sql
EXECUTE AS LOGIN = N'mkm_app';
BEGIN TRY
    UPDATE dbo.events SET actor = actor WHERE 1 = 0;
    PRINT '*** FAILED: the event log is writable ***';
END TRY
BEGIN CATCH
    PRINT 'Blocked as expected: ' + ERROR_MESSAGE();
END CATCH
REVERT;
```

Expect `The UPDATE permission was denied on the object 'events'` (error 229).

## What this does not cover

- **The owner/migration account can still alter the log**, by design — it has to be
  able to create the schema. Immutability is a property of the *runtime* account.
  Keep the owner credentials out of the application's configuration.
- **The hash chain is the detection half** and is application-level, so it crossed
  to SQL Server unchanged. These grants are the prevention half. An audit story
  wants both.
- **Backups are a separate gap on SQL Server** — `scripts/backup_db.sh` locates
  `pg_dump` and exits 0 when it cannot find one, so the hourly schedule reports
  success while doing nothing.

---

© 2022–2026 MKM Research Labs. Licensed under the MIT License.
