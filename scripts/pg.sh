#!/usr/bin/env bash
# Copyright (c) 2022-2026 MKM Research Labs. Licensed under the MIT License; see LICENSE.
#
# Manage a local native PostgreSQL cluster for MKM-ModelRisk (no Docker).
# Reads connection settings from .env when present; otherwise uses the defaults
# below (which match config/database.py).
#
#   scripts/pg.sh init     # create the cluster + the mkm_modelrisk database
#   scripts/pg.sh start     # start the cluster
#   scripts/pg.sh stop      # stop the cluster
#   scripts/pg.sh status    # is it accepting connections?
set -euo pipefail
cd "$(dirname "$0")/.."
[ -f .env ] && { set -a; . ./.env; set +a; }

if [ -n "${MKM_PG_BIN:-}" ]; then
  PGBIN="$MKM_PG_BIN"
elif [ -d /opt/homebrew/opt/postgresql@16/bin ]; then
  PGBIN=/opt/homebrew/opt/postgresql@16/bin   # Apple Silicon Homebrew
elif [ -d /usr/local/opt/postgresql@16/bin ]; then
  PGBIN=/usr/local/opt/postgresql@16/bin      # Intel Homebrew
else
  echo "postgresql@16 not found. Install with: brew install postgresql@16" >&2
  echo "Or set MKM_PG_BIN to the directory containing initdb/pg_ctl." >&2
  exit 1
fi
DATA="${MKM_PG_DATA_DIR:-$PWD/.pgdata}"
HOST="${MKM_DB_HOST:-127.0.0.1}"
PORT="${MKM_DB_PORT:-5433}"
OWNER="${MKM_DB_OWNER_USER:-mkm_owner}"
OWNER_PW="${MKM_DB_OWNER_PASSWORD:-mkm_dev_pw}"
DBNAME="${MKM_DB_NAME:-mkm_modelrisk}"
export PATH="$PGBIN:$PATH"
export LC_ALL="${LC_ALL:-en_US.UTF-8}" LANG="${LANG:-en_US.UTF-8}"

case "${1:-status}" in
  init)
    [ -d "$DATA" ] && { echo "Data dir already exists: $DATA" >&2; exit 1; }
    initdb -D "$DATA" -U "$OWNER" -A scram-sha-256 \
      --pwfile=<(printf '%s' "$OWNER_PW") --locale=en_US.UTF-8 -E UTF-8
    pg_ctl -D "$DATA" -o "-p $PORT" -l "$DATA/server.log" start
    sleep 2
    PGPASSWORD="$OWNER_PW" createdb -h "$HOST" -p "$PORT" -U "$OWNER" "$DBNAME"
    echo "Cluster ready on port $PORT; database '$DBNAME' created."
    ;;
  start)  pg_ctl -D "$DATA" -o "-p $PORT" -l "$DATA/server.log" start ;;
  stop)   pg_ctl -D "$DATA" stop ;;
  status) pg_isready -h "$HOST" -p "$PORT" ;;
  *)      echo "usage: $0 {init|start|stop|status}" >&2; exit 1 ;;
esac
