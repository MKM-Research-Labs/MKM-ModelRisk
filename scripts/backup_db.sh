#!/usr/bin/env bash
# Copyright (c) 2022-2026 MKM Research Labs. Licensed under the MIT License; see LICENSE.
#
# Hourly (or on-demand) backup of the ModelRisk estate: the Postgres database, and
# the uploaded documents the governance record references.
#
# Writes a timestamped custom-format dump to the backup directory on the INTERNAL
# disk, so a backup survives the external SSD being unmounted or failing (the live
# cluster lives on the SSD). Safe to run when the DB is down: if the cluster is not
# reachable — SSD unmounted, Postgres stopped — it logs a skip and exits 0 rather
# than erroring, so a scheduler firing every hour never generates noise.
#
# Reads DB credentials from the repo .env (never hard-coded). Retention: keeps the
# last RETAIN_DAYS of hourly dumps and prunes older ones.
#
# Usage:  bash scripts/backup_db.sh
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"

# --- credentials from .env ------------------------------------------------------
if [ ! -f .env ]; then
  echo "$(date '+%F %T')  no .env — cannot resolve DB credentials; skipping" >&2
  exit 0
fi
# shellcheck disable=SC1091
set -a; . ./.env; set +a
HOST="${DB_HOST:-localhost}"; PORT="${DB_PORT:-5433}"
NAME="${DB_NAME:-mkm_modelrisk}"; OWNER="${DB_OWNER_USER:-mkm_owner}"

# --- locate pg_dump (mirrors scripts/pg.sh) -------------------------------------
if [ -n "${PG_BIN:-}" ]; then PGBIN="$PG_BIN"
elif [ -d /opt/homebrew/opt/postgresql@16/bin ]; then PGBIN=/opt/homebrew/opt/postgresql@16/bin
elif [ -d /usr/local/opt/postgresql@16/bin ]; then PGBIN=/usr/local/opt/postgresql@16/bin
elif [ -d /usr/lib/postgresql/16/bin ]; then PGBIN=/usr/lib/postgresql/16/bin
elif [ -d /usr/pgsql-16/bin ]; then PGBIN=/usr/pgsql-16/bin
elif command -v pg_dump >/dev/null 2>&1; then PGBIN="$(dirname "$(command -v pg_dump)")"
else echo "$(date '+%F %T')  pg_dump not found; skipping" >&2; exit 0; fi

# --- destination on the internal disk -------------------------------------------
BACKUP_DIR="${BACKUP_DIR:-$REPO/../ModelRisk-backups/hourly}"
RETAIN_DAYS="${RETAIN_DAYS:-7}"
mkdir -p "$BACKUP_DIR"
LOG="$BACKUP_DIR/backup.log"

log() { echo "$(date '+%F %T')  $*" | tee -a "$LOG" >&2; }

# --- skip cleanly when the cluster is not reachable -----------------------------
export PGPASSWORD="${DB_OWNER_PASSWORD:-}"
# Reachability probe only — the real auth happens in pg_dump below. PGPASSWORD is
# exported above, and with a password in the environment pg_isready authenticates
# (as the OS user, libpq's default, since no role is named) and fails noisily in
# the server log. Drop PGPASSWORD for the probe so it just checks the port is up.
if ! env -u PGPASSWORD "$PGBIN/pg_isready" -h "$HOST" -p "$PORT" >/dev/null 2>&1; then
  log "database not reachable (SSD unmounted or Postgres stopped) — skipped"
  exit 0
fi

# --- dump -----------------------------------------------------------------------
STAMP="$(date -u '+%Y%m%d-%H%M%S')"
OUT="$BACKUP_DIR/${NAME}-${STAMP}.dump"
if "$PGBIN/pg_dump" -Fc -h "$HOST" -p "$PORT" -U "$OWNER" -d "$NAME" -f "$OUT" 2>>"$LOG"; then
  SIZE="$(wc -c <"$OUT" | tr -d ' ')"
  log "backup OK: $OUT ($SIZE bytes)"
else
  log "backup FAILED — pg_dump error (see log above)"
  rm -f "$OUT"
  exit 1
fi

# --- mirror the uploaded documents ----------------------------------------------
# pg_dump captures the governance record; the documents it references live on disk
# and are in no dump. Restoring without them yields a record full of dangling
# references — evidence packs pointing at files that no longer exist — so the
# documents are mirrored alongside every dump.
#
# Deliberately AFTER the dump. A document is written to disk before the event that
# references it is appended, so a file arriving between the two lands in the mirror
# while no dump references it yet — a harmless orphan. Mirroring first would invert
# that into the damaging case: a dump referencing a file the mirror never captured.
#
# No --delete: the mirror only ever grows. The dumps are the point-in-time record;
# this is the evidence behind them, and a document removed from the live tree must
# not vanish from the backups that older dumps still reference.
UPLOADS="${UPLOAD_DIR:-$REPO/uploads}"
MIRROR="${UPLOADS_MIRROR:-$BACKUP_DIR/../uploads}"
if [ -d "$UPLOADS" ]; then
  mkdir -p "$MIRROR"
  if rsync -a "$UPLOADS/" "$MIRROR/" 2>>"$LOG"; then
    FILES="$(find "$MIRROR" -type f | wc -l | tr -d ' ')"
    log "uploads mirrored -> $MIRROR ($FILES files)"
  else
    log "uploads mirror FAILED — rsync error (see log above)"
  fi
else
  log "no uploads directory at $UPLOADS — nothing to mirror"
fi

# --- prune old dumps ------------------------------------------------------------
find "$BACKUP_DIR" -name "${NAME}-*.dump" -type f -mtime "+${RETAIN_DAYS}" -print -delete 2>/dev/null \
  | while read -r p; do log "pruned old backup: $p"; done || true
