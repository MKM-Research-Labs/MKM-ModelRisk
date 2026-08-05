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
"""Backfill: add the standing "Governance completeness audit" agenda item to
meetings that were scheduled before the item existed.

New meetings seed it automatically (``seed_standing_agenda``); only open meetings
already on the record miss it. Idempotent and re-runnable: a meeting that already
has the item — or one that is already closed (immutable) — is left alone.

Run against the configured ModelRisk database:

    python -m scripts.backfill_completeness_audit_item
"""
from __future__ import annotations

from config.governance import CLOSED_MEETING_STATUS, STANDING_AGENDA
from src.governance.mrc import add_collection_item, list_meetings, rebuild_meeting_view

ACTOR = "backfill_completeness_audit_item"
AUDIT_KIND = "completeness_audit"
_TEMPLATE = next(i for i in STANDING_AGENDA if i["kind"] == AUDIT_KIND)


def _has_audit_item(data: dict) -> bool:
    return any(a.get("kind") == AUDIT_KIND for a in (data.get("agenda") or []))


def backfill(config=None) -> dict:
    added = skipped = 0
    for meeting in list_meetings(config=config):
        data = meeting.get("data") or {}
        if data.get("status") == CLOSED_MEETING_STATUS or _has_audit_item(data):
            skipped += 1
            continue
        add_collection_item(
            meeting_id=meeting["meeting_id"], collection="agenda",
            fields=dict(_TEMPLATE), actor=ACTOR, config=config)
        added += 1
    rebuild_meeting_view(config=config)
    return {"added": added, "skipped": skipped}


def main() -> int:
    from src.database import run_migrations
    run_migrations()
    result = backfill()
    print(f"completeness-audit items added: {result['added']}, "
          f"skipped (closed or already present): {result['skipped']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
