#!/usr/bin/env bash
# Copyright (c) 2022-2026 MKM Research Labs. Licensed under the MIT License; see LICENSE.
#
# Build a scratch database from the newest hourly backup, for testing and for the
# verification app (coding rule R9). The live database is the governance record and its
# event log is append-only, so nothing throwaway may write to it — work against a copy.
#
#   scripts/restore_scratch.sh                  # newest dump -> mkm_modelrisk_scratch
#   scripts/restore_scratch.sh <dump>           # a specific dump
#   SCRATCH_DB=other scripts/restore_scratch.sh # a different scratch name
#
# Then point the app or a script at it:
#   set -a; . ./.env; set +a; export DB_NAME=mkm_modelrisk_scratch
#
# Note the ordering trap this script deliberately avoids: scripts/pg.sh sources .env AFTER
# the caller's environment, so `DB_NAME=scratch scripts/pg.sh restore` would restore over
# the LIVE database. Here the target is passed explicitly to pg_restore and refused if it
# is a protected name.
set -euo pipefail

cd "$(dirname "$0")/.."
[ -f .env ] && { set -a; . ./.env; set +a; }

# Names holding real data. Mirrors config/database.py PROTECTED_DB_NAMES — the one list
# both the app and this script refuse to touch.
PROTECTED="mkm_modelrisk mkm_modelrisk_demo"

SCRATCH="${SCRATCH_DB:-mkm_modelrisk_scratch}"
for name in $PROTECTED; do
  [ "$SCRATCH" = "$name" ] && {
    echo "Refusing to restore over '$SCRATCH': it holds real data." >&2; exit 1; }
done

if [ -n "${PG_BIN:-}" ]; then PGBIN="$PG_BIN"
elif [ -d /opt/homebrew/opt/postgresql@16/bin ]; then PGBIN=/opt/homebrew/opt/postgresql@16/bin
elif [ -d /usr/local/opt/postgresql@16/bin ]; then PGBIN=/usr/local/opt/postgresql@16/bin
elif command -v pg_restore >/dev/null 2>&1; then PGBIN="$(dirname "$(command -v pg_restore)")"
else echo "PostgreSQL 16 not found; set PG_BIN." >&2; exit 1; fi

HOST="${DB_HOST:-127.0.0.1}"
PORT="${DB_PORT:-5433}"
OWNER="${DB_OWNER_USER:-mkm_owner}"
OWNER_PW="${DB_OWNER_PASSWORD:-mkm_dev_pw}"
SOURCE_DB="${DB_NAME:-mkm_modelrisk}"
BACKUP_DIR="${BACKUP_DIR:-$PWD/../ModelRisk-backups/hourly}"

DUMP="${1:-}"
if [ -z "$DUMP" ]; then
  DUMP="$(ls -t "$BACKUP_DIR/${SOURCE_DB}-"*.dump 2>/dev/null | head -1 || true)"
fi
[ -n "$DUMP" ] && [ -f "$DUMP" ] || {
  echo "No dump found. Looked in $BACKUP_DIR for ${SOURCE_DB}-*.dump" >&2
  echo "Take one with: scripts/pg.sh backup" >&2; exit 1; }

export PGPASSWORD="$OWNER_PW"
echo "Restoring $(basename "$DUMP") -> '$SCRATCH'" >&2

# Recreate the scratch database so a restore never layers onto stale contents.
"$PGBIN/psql" -h "$HOST" -p "$PORT" -U "$OWNER" -d postgres -v ON_ERROR_STOP=1 \
  -c "DROP DATABASE IF EXISTS \"$SCRATCH\";" \
  -c "CREATE DATABASE \"$SCRATCH\" OWNER \"$OWNER\";" >/dev/null

# Grants are restored, not stripped: the app connects as a non-owner role, and the dump's
# ACLs carry the event log's revoked UPDATE/DELETE — the immutability control the scratch
# copy should reproduce, so behaviour here matches production. --no-owner only avoids
# reassigning object ownership.
"$PGBIN/pg_restore" --no-owner -h "$HOST" -p "$PORT" -U "$OWNER" \
  -d "$SCRATCH" "$DUMP" 2>&1 | grep -v "^pg_restore: warning" || true

echo >&2
echo "Ready. Point work at it with:" >&2
echo "  set -a; . ./.env; set +a; export DB_NAME=$SCRATCH" >&2
echo "Confirm before the first write:" >&2
echo "  python -c \"from config.database import DatabaseConfig; print(DatabaseConfig.from_env().name)\"" >&2
