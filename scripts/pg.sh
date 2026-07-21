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
# Pick a UTF-8 locale that actually exists. Minimal Linux images frequently ship
# without en_US.UTF-8, and initdb fails outright on an unknown locale.
if [ -z "${MKM_PG_LOCALE:-}" ]; then
  if locale -a 2>/dev/null | grep -qiE '^en_US\.utf-?8$'; then
    MKM_PG_LOCALE=en_US.UTF-8
  elif locale -a 2>/dev/null | grep -qiE '^C\.utf-?8$'; then
    MKM_PG_LOCALE=C.UTF-8
  else
    MKM_PG_LOCALE=C
  fi
fi
export LC_ALL="$MKM_PG_LOCALE" LANG="$MKM_PG_LOCALE"

case "${1:-status}" in
  init)
    [ -d "$DATA" ] && { echo "Data dir already exists: $DATA" >&2; exit 1; }
    initdb -D "$DATA" -U "$OWNER" -A scram-sha-256 \
      --pwfile=<(printf '%s' "$OWNER_PW") --locale="$MKM_PG_LOCALE" -E UTF-8
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
