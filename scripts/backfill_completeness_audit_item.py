# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Sync the standing "Governance completeness audit" agenda item onto meetings
scheduled before it existed (or before its wording changed).

New meetings seed it automatically (``seed_standing_agenda``); this keeps the
open meetings already on the record in step. Idempotent and re-runnable on each
open meeting: add the item if missing, refresh its title/description if they have
drifted from the current template, otherwise leave it alone. Closed meetings are
immutable and skipped.

Run against the configured ModelRisk database:

    python -m scripts.backfill_completeness_audit_item
"""
from __future__ import annotations

from config.governance import CLOSED_MEETING_STATUS, STANDING_AGENDA
from src.governance.mrc import (
    add_collection_item, list_meetings, rebuild_meeting_view, update_collection_item)

ACTOR = "backfill_completeness_audit_item"
AUDIT_KIND = "completeness_audit"
_TEMPLATE = next(i for i in STANDING_AGENDA if i["kind"] == AUDIT_KIND)
# The template fields whose current wording should be carried onto existing items.
_TEXT_FIELDS = ("title", "description")


def _audit_item(data: dict) -> dict | None:
    return next((a for a in (data.get("agenda") or []) if a.get("kind") == AUDIT_KIND), None)


def _stale_text(item: dict) -> dict:
    """Template title/description that differ from what the item currently holds."""
    return {k: _TEMPLATE[k] for k in _TEXT_FIELDS if item.get(k) != _TEMPLATE.get(k)}


def backfill(config=None) -> dict:
    added = refreshed = skipped = 0
    for meeting in list_meetings(config=config):
        data = meeting.get("data") or {}
        if data.get("status") == CLOSED_MEETING_STATUS:
            skipped += 1
            continue
        item = _audit_item(data)
        if item is None:
            add_collection_item(
                meeting_id=meeting["meeting_id"], collection="agenda",
                fields=dict(_TEMPLATE), actor=ACTOR, config=config)
            added += 1
            continue
        stale = _stale_text(item)
        if stale:
            update_collection_item(
                meeting_id=meeting["meeting_id"], collection="agenda",
                item_id=item["item_id"], fields=stale, actor=ACTOR, config=config)
            refreshed += 1
        else:
            skipped += 1
    rebuild_meeting_view(config=config)
    return {"added": added, "refreshed": refreshed, "skipped": skipped}


def main() -> int:
    from src.database import run_migrations
    run_migrations()
    result = backfill()
    print(f"completeness-audit items added: {result['added']}, "
          f"descriptions refreshed: {result['refreshed']}, "
          f"skipped (closed or already current): {result['skipped']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
