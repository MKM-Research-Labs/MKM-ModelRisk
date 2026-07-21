#!/usr/bin/env bash
# Copyright (c) 2022-2026 MKM Research Labs. Licensed under the MIT License; see LICENSE.
#
# One-command setup for MKM-ModelRisk on Linux and macOS. Checks the toolchain,
# creates the virtualenv, installs dependencies, brings up the local PostgreSQL
# cluster, then launches the app. Safe to re-run — every step is idempotent.
#
#   bash scripts/start.sh                 # set everything up, then run the app
#   bash scripts/start.sh --no-run        # set up only, don't launch
#   bash scripts/start.sh --seed          # also load the example models
#   bash scripts/start.sh --identity me@corp
set -euo pipefail
cd "$(dirname "$0")/.."

RUN_APP=1
SEED=0
step() { printf '\n\033[1m==> %s\033[0m\n' "$1"; }
fail() { printf '\033[31mERROR: %s\033[0m\n' "$1" >&2; exit 1; }

while [ $# -gt 0 ]; do
  case "$1" in
    --no-run)  RUN_APP=0 ;;
    --seed)    SEED=1 ;;
    --identity) shift; export IDENTITY_DEV_FALLBACK="${1:-}" ;;
    -h|--help) sed -n '4,11p' "$0"; exit 0 ;;
    *) fail "unknown option: $1 (try --help)" ;;
  esac
  shift
done

# --- 1. Python 3.13+ -------------------------------------------------------
step "Checking Python"
PY=""
for candidate in python3.13 python3 python; do
  if command -v "$candidate" >/dev/null 2>&1 \
     && "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3,13) else 1)' 2>/dev/null; then
    PY="$candidate"; break
  fi
done
[ -n "$PY" ] || fail "Python 3.13+ not found. Install it:
  Debian/Ubuntu:  sudo apt install python3.13 python3.13-venv
                  (Ubuntu <=24.04 ships 3.12 — add ppa:deadsnakes/ppa first)
  Fedora/RHEL:    sudo dnf install python3.13
  macOS:          brew install python@3.13"
echo "using $($PY --version) at $(command -v "$PY")"

# --- 2. Virtualenv + dependencies -----------------------------------------
step "Setting up the virtualenv (.venv)"
if [ ! -d .venv ]; then
  "$PY" -m venv .venv \
    || fail "could not create the virtualenv. On Debian/Ubuntu install the venv module:
  sudo apt install python3.13-venv"
fi
# shellcheck disable=SC1091
. .venv/bin/activate
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -e ".[dev]"
echo "dependencies installed"

# --- 3. PostgreSQL cluster -------------------------------------------------
step "Starting the PostgreSQL cluster"
DATA="${PG_DATA_DIR:-$PWD/.pgdata}"
if bash scripts/pg.sh status >/dev/null 2>&1; then
  echo "a cluster is already serving port ${DB_PORT:-5433} — leaving it alone"
elif [ -d "$DATA" ]; then
  bash scripts/pg.sh start
else
  bash scripts/pg.sh init
fi
bash scripts/pg.sh status >/dev/null 2>&1 \
  || fail "the database is not accepting connections. Run 'bash scripts/pg.sh status' to see why."
echo "cluster is accepting connections on port ${DB_PORT:-5433}"

# --- 4. Identity used for the audit trail ---------------------------------
if [ -z "${IDENTITY_DEV_FALLBACK:-}" ] && [ -t 0 ]; then
  read -rp $'\nIdentity your changes are attributed to [dev@localhost]: ' ID || true
  export IDENTITY_DEV_FALLBACK="${ID:-dev@localhost}"
fi

if [ "$SEED" = "1" ]; then
  step "Seeding example models"
  python scripts/seed_demo.py
fi

# --- 5. Run ----------------------------------------------------------------
if [ "$RUN_APP" = "1" ]; then
  step "Starting MKM-ModelRisk on http://${WEB_HOST:-127.0.0.1}:${WEB_PORT:-5015}"
  exec python app.py
fi
step "Setup complete"
cat <<EOF
To start the app:
  source .venv/bin/activate
  python app.py
Then open http://${WEB_HOST:-127.0.0.1}:${WEB_PORT:-5015}
EOF
