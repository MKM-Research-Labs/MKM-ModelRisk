#!/usr/bin/env bash
# Copyright (c) 2022-2026 MKM Research Labs. Licensed under the MIT License; see LICENSE.
#
# Manage a local native PostgreSQL cluster for MKM-ModelRisk (no Docker).
# Reads connection settings from .env when present; otherwise uses the defaults
# below (which match config/database.py).
#
#   scripts/pg.sh init            # create the cluster + the mkm_modelrisk database
#   scripts/pg.sh start           # start the cluster
#   scripts/pg.sh stop            # stop the cluster
#   scripts/pg.sh status          # is it accepting connections?
#   scripts/pg.sh backup          # dump the database to the internal-disk backups
#   scripts/pg.sh restore <dump>  # safety-backup, then restore a dump (--clean)
#   scripts/pg.sh reset [--force] # backup, confirm, then drop + recreate the DB
#
# reset and restore always take a safety backup first, so clearing the database
# (e.g. to test against an empty instance) is never irreversible. Use a separate
# DB_NAME for throwaway testing rather than resetting the demo database.
set -euo pipefail
cd "$(dirname "$0")/.."
[ -f .env ] && { set -a; . ./.env; set +a; }

if [ -n "${PG_BIN:-}" ]; then
  PGBIN="$PG_BIN"
elif [ -d /opt/homebrew/opt/postgresql@16/bin ]; then
  PGBIN=/opt/homebrew/opt/postgresql@16/bin   # Apple Silicon Homebrew
elif [ -d /usr/local/opt/postgresql@16/bin ]; then
  PGBIN=/usr/local/opt/postgresql@16/bin      # Intel Homebrew
elif [ -d /usr/lib/postgresql/16/bin ]; then
  PGBIN=/usr/lib/postgresql/16/bin            # Debian / Ubuntu
elif [ -d /usr/pgsql-16/bin ]; then
  PGBIN=/usr/pgsql-16/bin                     # RHEL / Fedora (PGDG)
elif command -v initdb >/dev/null 2>&1; then
  PGBIN="$(dirname "$(command -v initdb)")"   # already on PATH
else
  echo "PostgreSQL 16 not found. Install it with one of:" >&2
  echo "  macOS:          brew install postgresql@16" >&2
  echo "  Debian/Ubuntu:  sudo apt install postgresql-16" >&2
  echo "  Fedora/RHEL:    sudo dnf install postgresql16-server" >&2
  echo "Or set PG_BIN to the directory containing initdb/pg_ctl." >&2
  exit 1
fi
DATA="${PG_DATA_DIR:-$PWD/.pgdata}"
HOST="${DB_HOST:-127.0.0.1}"
PORT="${DB_PORT:-5433}"
OWNER="${DB_OWNER_USER:-mkm_owner}"
OWNER_PW="${DB_OWNER_PASSWORD:-mkm_dev_pw}"
DBNAME="${DB_NAME:-mkm_modelrisk}"
export PATH="$PGBIN:$PATH"
# Pick a UTF-8 locale that actually exists. Minimal Linux images frequently ship
# without en_US.UTF-8, and initdb fails outright on an unknown locale.
if [ -z "${PG_LOCALE:-}" ]; then
  if locale -a 2>/dev/null | grep -qiE '^en_US\.utf-?8$'; then
    PG_LOCALE=en_US.UTF-8
  elif locale -a 2>/dev/null | grep -qiE '^C\.utf-?8$'; then
    PG_LOCALE=C.UTF-8
  else
    PG_LOCALE=C
  fi
fi
export LC_ALL="$PG_LOCALE" LANG="$PG_LOCALE"

case "${1:-status}" in
  init)
    [ -d "$DATA" ] && { echo "Data dir already exists: $DATA" >&2; exit 1; }
    initdb -D "$DATA" -U "$OWNER" -A scram-sha-256 \
      --pwfile=<(printf '%s' "$OWNER_PW") --locale="$PG_LOCALE" -E UTF-8
    pg_ctl -D "$DATA" -o "-p $PORT" -l "$DATA/server.log" start
    sleep 2
    PGPASSWORD="$OWNER_PW" createdb -h "$HOST" -p "$PORT" -U "$OWNER" "$DBNAME"
    echo "Cluster ready on port $PORT; database '$DBNAME' created."
    ;;
  start)
    # Idempotent: starting an already-running cluster is a no-op, not an error.
    # pg_ctl would otherwise fail with "could not start server", which reads as a
    # fault when nothing is wrong.
    if pg_isready -h "$HOST" -p "$PORT" >/dev/null 2>&1; then
      echo "Cluster already accepting connections on port $PORT."
    else
      pg_ctl -D "$DATA" -o "-p $PORT" -l "$DATA/server.log" start
    fi
    ;;
  stop)
    if pg_isready -h "$HOST" -p "$PORT" >/dev/null 2>&1; then
      pg_ctl -D "$DATA" stop
    else
      echo "No cluster is running on port $PORT."
    fi
    ;;
  status) pg_isready -h "$HOST" -p "$PORT" ;;

  backup) exec bash "$(dirname "$0")/backup_db.sh" ;;

  restore)
    DUMP="${2:-}"
    [ -n "$DUMP" ] && [ -f "$DUMP" ] || { echo "usage: $0 restore <dump-file>" >&2; exit 1; }
    echo "Safety backup of '$DBNAME' before restore..." >&2
    bash "$(dirname "$0")/backup_db.sh" || echo "  (safety backup skipped) " >&2
    echo "Restoring $DUMP into '$DBNAME'..." >&2
    PGPASSWORD="$OWNER_PW" pg_restore --clean --if-exists --no-owner \
      -h "$HOST" -p "$PORT" -U "$OWNER" -d "$DBNAME" "$DUMP"
    echo "Restore complete. Start the app to apply any newer migrations." >&2
    ;;

  reset)
    # A sanctioned, recoverable reset: dropping the database is fine to do, but a
    # raw 'dropdb' is how the demo was lost once. This backs up first, then makes
    # you confirm by typing the name — so an accidental reset is impossible and a
    # deliberate one is always restorable from the backup just taken.
    echo "reset DROPS and recreates '$DBNAME' — all current data is lost." >&2
    bash "$(dirname "$0")/backup_db.sh" || echo "  (safety backup skipped) " >&2
    if [ "${2:-}" != "--force" ]; then
      printf "Type the database name to confirm [%s]: " "$DBNAME" >&2
      read -r ans
      [ "$ans" = "$DBNAME" ] || { echo "Aborted — nothing changed." >&2; exit 1; }
    fi
    PGPASSWORD="$OWNER_PW" dropdb --if-exists -f -h "$HOST" -p "$PORT" -U "$OWNER" "$DBNAME"
    PGPASSWORD="$OWNER_PW" createdb -h "$HOST" -p "$PORT" -U "$OWNER" "$DBNAME"
    echo "'$DBNAME' reset. Start the app to apply migrations and seed reference data." >&2
    ;;

  *)      echo "usage: $0 {init|start|stop|status|backup|restore <dump>|reset [--force]}" >&2; exit 1 ;;
esac
