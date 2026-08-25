#!/usr/bin/env bash
# Copyright (c) 2022-2026 MKM Research Labs. Licensed under the MIT License; see LICENSE.
#
# The verification app: port 5016, scratch database, never production (coding rule R9).
# Port 5015 serves the live estate; everything under test runs here instead.
#
#   scripts/restore_scratch.sh     # refresh the scratch DB from the newest backup
#   scripts/dev_app.sh             # serve it on 5016
#
# The port is a convention; the guard below is what actually protects the estate. This
# refuses to start against a protected database however DB_NAME was set — including the
# common accident of sourcing .env (which points at mkm_modelrisk) and forgetting to
# override it. A verification app on 5016 pointed at production is the exact mistake that
# put junk models into the live event log on 2026-08-06.
set -euo pipefail

cd "$(dirname "$0")/.."
[ -f .env ] && { set -a; . ./.env; set +a; }

# Mirrors config/database.py PROTECTED_DB_NAMES.
PROTECTED="mkm_modelrisk mkm_modelrisk_demo"

# .env has just overwritten DB_NAME, so set the scratch target AFTER sourcing it.
export DB_NAME="${SCRATCH_DB:-mkm_modelrisk_scratch}"
export WEB_PORT="${WEB_PORT:-5016}"
export WEB_HOST="${WEB_HOST:-127.0.0.1}"

# No backup schedule from the verification app. backup_db.sh takes its credentials
# from .env, so it would dump the LIVE database while this app serves a scratch
# copy — a schedule the estate's real app is already keeping.
export BACKUP_ENABLED=0

for name in $PROTECTED; do
  [ "$DB_NAME" = "$name" ] && {
    echo "REFUSING TO START: DB_NAME is '$DB_NAME', which holds the real estate." >&2
    echo "Build a scratch copy first:  scripts/restore_scratch.sh" >&2
    exit 1; }
done

PY="${PYTHON:-.venv/bin/python}"
RESOLVED="$("$PY" -c 'from config.database import DatabaseConfig; print(DatabaseConfig.from_env().name)')"
for name in $PROTECTED; do
  [ "$RESOLVED" = "$name" ] && {
    echo "REFUSING TO START: config resolves to '$RESOLVED' despite DB_NAME='$DB_NAME'." >&2
    exit 1; }
done

echo "Verification app: http://$WEB_HOST:$WEB_PORT   database: $RESOLVED" >&2

# Served by gunicorn, exactly as the real thing is, so what is verified here is
# what ships — including the WSGI startup path (one bootstrap in the master, then
# the fork). Settings come from gunicorn.conf.py, which reads WEB_HOST/WEB_PORT
# exported above.
# --bind is already set from WEB_BIND in gunicorn.conf.py; passing it again puts the
# PORT on this process's command line, which is what tells this app apart from the
# estate's in ``ps``/``pgrep``. gunicorn's own proc_name cannot: it is a no-op unless
# setproctitle is installed. The control socket is separated in config/web.py.
exec "$PY" -m gunicorn --config gunicorn.conf.py --bind "$WEB_HOST:$WEB_PORT" wsgi:application
