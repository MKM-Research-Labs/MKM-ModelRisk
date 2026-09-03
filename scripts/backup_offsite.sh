#!/usr/bin/env bash
# Copyright (c) 2022-2026 MKM Research Labs. Licensed under the MIT License; see LICENSE.
#
# Daily off-machine copy of the ModelRisk backups.
#
# scripts/backup_db.sh writes its dumps and its uploads mirror to the internal disk,
# which protects against the cluster's volume failing but not against the machine
# failing. This pushes both to iCloud Drive, so the governance record survives the
# loss of the Mac it is served from.
#
# Retention differs from the hourly script on purpose. Locally RETAIN_DAYS is short
# because dumps accumulate every hour; off-site keeps ONE dump per day for far
# longer, which is the copy you actually reach for when a corruption is noticed
# weeks after the fact.
#
# Safe to run when nothing has changed, when iCloud is unavailable, or twice in a
# day: it logs and exits 0 rather than erroring, so a scheduler never generates
# noise.
#
# Usage:  bash scripts/backup_offsite.sh
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"

[ -f .env ] && { set -a; . ./.env; set +a; }

BACKUP_DIR="${BACKUP_DIR:-$REPO/../ModelRisk-backups/hourly}"
MIRROR="${UPLOADS_MIRROR:-$BACKUP_DIR/../uploads}"
NAME="${DB_NAME:-mkm_modelrisk}"

ICLOUD="${ICLOUD_DIR:-$HOME/Library/Mobile Documents/com~apple~CloudDocs}"
OFFSITE="${OFFSITE_DIR:-$ICLOUD/ModelRisk-backups}"
OFFSITE_RETAIN_DAYS="${OFFSITE_RETAIN_DAYS:-30}"

LOG="${OFFSITE_LOG:-$BACKUP_DIR/offsite.log}"
mkdir -p "$(dirname "$LOG")"
log() { echo "$(date '+%F %T')  $*" | tee -a "$LOG" >&2; }

# iCloud Drive is a normal directory, but it is absent on a Mac not signed in to
# iCloud — and creating it there would silently write to a path that never syncs.
if [ ! -d "$ICLOUD" ]; then
  log "iCloud Drive not present at $ICLOUD — skipped"
  exit 0
fi

mkdir -p "$OFFSITE/dumps" "$OFFSITE/uploads"

# --- one dump per day ------------------------------------------------------------
# The hourly script leaves ~24 dumps a day; copying them all would push a GB a month
# into iCloud for no recovery benefit. Take the newest.
NEWEST="$(ls -t "$BACKUP_DIR/${NAME}-"*.dump 2>/dev/null | head -1 || true)"
if [ -n "$NEWEST" ] && [ -f "$NEWEST" ]; then
  DEST="$OFFSITE/dumps/$(basename "$NEWEST")"
  if [ -f "$DEST" ]; then
    log "dump already off-site: $(basename "$NEWEST")"
  elif rsync -a "$NEWEST" "$DEST" 2>>"$LOG"; then
    log "dump copied off-site: $(basename "$NEWEST") ($(wc -c <"$DEST" | tr -d ' ') bytes)"
  else
    log "dump copy FAILED — rsync error (see log above)"
  fi
else
  log "no dump found in $BACKUP_DIR — nothing to copy"
fi

# --- the documents ---------------------------------------------------------------
# No --delete, for the same reason as the local mirror: an off-site copy that forgets
# a document the moment it leaves the live tree is not a backup of an append-only
# record.
if [ -d "$MIRROR" ]; then
  if rsync -a "$MIRROR/" "$OFFSITE/uploads/" 2>>"$LOG"; then
    FILES="$(find "$OFFSITE/uploads" -type f | wc -l | tr -d ' ')"
    log "uploads copied off-site -> $OFFSITE/uploads ($FILES files)"
  else
    log "uploads copy FAILED — rsync error (see log above)"
  fi
else
  log "no uploads mirror at $MIRROR — run scripts/backup_db.sh first"
fi

# --- prune old off-site dumps ----------------------------------------------------
find "$OFFSITE/dumps" -name "${NAME}-*.dump" -type f -mtime "+${OFFSITE_RETAIN_DAYS}" \
  -print -delete 2>/dev/null \
  | while read -r p; do log "pruned off-site dump: $p"; done || true
