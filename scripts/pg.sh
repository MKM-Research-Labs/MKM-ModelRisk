#!/usr/bin/env bash
# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
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

PGBIN="${MKM_PG_BIN:-/opt/homebrew/opt/postgresql@16/bin}"
DATA="${MKM_PG_DATA_DIR:-$PWD/.pgdata}"
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
    PGPASSWORD="$OWNER_PW" createdb -h 127.0.0.1 -p "$PORT" -U "$OWNER" "$DBNAME"
    echo "Cluster ready on port $PORT; database '$DBNAME' created."
    ;;
  start)  pg_ctl -D "$DATA" -o "-p $PORT" -l "$DATA/server.log" start ;;
  stop)   pg_ctl -D "$DATA" stop ;;
  status) pg_isready -h 127.0.0.1 -p "$PORT" ;;
  *)      echo "usage: $0 {init|start|stop|status}" >&2; exit 1 ;;
esac
