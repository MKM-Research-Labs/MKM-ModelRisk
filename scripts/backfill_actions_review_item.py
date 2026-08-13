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
"""Introduce the standing "Review of outstanding actions" item to an estate that
predates it — the committee's agenda list first, then the meetings already scheduled.

Adding a kind to ``STANDING_AGENDA`` is not enough on its own. A committee's running
order lives in an admin-managed list (Admin > Agenda), and the first-run seed
deliberately seeds a vacuum rather than reconciling a curated list — so an estate that
already has an agenda would never see a newly-shipped item, and neither would any
meeting scheduled from it.

Both halves are idempotent, and neither overrules a curator: the item is added only
where its ``kind`` is absent, and a list that already has one (wherever it has been
moved to) is left exactly as it is. Closed meetings are immutable and skipped.

Run against the configured ModelRisk database:

    python -m scripts.backfill_actions_review_item
"""
from __future__ import annotations

from config.governance import (
    CLOSED_MEETING_STATUS, STANDING_AGENDA, STANDING_AGENDA_LIST)
from src.governance.mrc import (
    add_collection_item, list_meetings, rebuild_meeting_view)
from src.governance.reference import add_option, get_reference_lists, move_option

ACTOR = "backfill_actions_review_item"
REVIEW_KIND = "actions_review"
# The item sits directly after the minutes sign-off: the first thing a committee does
# once it has accepted the record is ask what it is still owed.
AFTER_KIND = "minutes_signoff"
_TEMPLATE = next(i for i in STANDING_AGENDA if i["kind"] == REVIEW_KIND)


def _has_kind(rows: list[dict], kind: str) -> bool:
    return any((r.get("kind") or "") == kind for r in rows)


def backfill_agenda_list(config=None) -> str:
    """Add the item to the committee's running order, just after the minutes sign-off.

    An empty list is left empty: the first-run seed will fill it from the shipped
    order, which now includes this item anyway.
    """
    rows = get_reference_lists(config=config).get(STANDING_AGENDA_LIST) or []
    if not rows:
        return "list empty — the first-run seed will supply the current order"
    if _has_kind(rows, REVIEW_KIND):
        return "already on the agenda list"
    add_option(list_name=STANDING_AGENDA_LIST, fields=dict(_TEMPLATE), actor=ACTOR,
               reason="Introduce the standing review of outstanding actions", config=config)
    # add_option appends, so walk it up to sit behind the minutes sign-off. Where there
    # is no minutes item to sit behind, leaving it at the end is the honest outcome —
    # better a curator moves it than this guesses at a position.
    rows = get_reference_lists(config=config).get(STANDING_AGENDA_LIST) or []
    target = next((i for i, r in enumerate(rows) if (r.get("kind") or "") == AFTER_KIND), None)
    if target is None:
        return "added at the end (no minutes sign-off item to follow)"
    added = next(r for r in rows if (r.get("kind") or "") == REVIEW_KIND)
    for _ in range(len(rows) - 1 - (target + 1)):
        move_option(list_name=STANDING_AGENDA_LIST, item_id=added["item_id"],
                    direction="up", actor=ACTOR, config=config)
    return f"added after the {AFTER_KIND} item"


def backfill_meetings(config=None) -> dict:
    """Add the item to every open meeting that has not got one."""
    added = skipped = 0
    for meeting in list_meetings(config=config):
        data = meeting.get("data") or {}
        if data.get("status") == CLOSED_MEETING_STATUS:
            skipped += 1
            continue
        if _has_kind(data.get("agenda") or [], REVIEW_KIND):
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
    print("agenda list: " + backfill_agenda_list())
    result = backfill_meetings()
    print(f"meetings updated: {result['added']}, "
          f"skipped (closed or already present): {result['skipped']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
