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
"""Backfill: a version register row for every version the change history records.

A model carries two registers. The version register is the timeline — what existed,
when, and against which document. The change history says what each release changed.
They drifted: a version can be minuted as a change without ever being added to the
timeline, which leaves a model reporting a current version its own register has
never heard of.

This adds the missing timeline rows, and ONLY those it can derive: for each change
history entry whose version is absent from the register, a row carrying that entry's
own date, description and author. Nothing is invented — a version with no change
history entry to derive from is reported and skipped, because a governance record
should not be filled in by guesswork.

Idempotent: a version already in the register is left alone, so re-running adds
nothing. Dry by default — it prints what it would add and writes nothing:

    python -m scripts.backfill_version_register            # show the gaps
    python -m scripts.backfill_version_register --apply    # record them

The events are attributed to ``--actor`` (default below). Pass your own identity if
you want the register to show who filled it.
"""
from __future__ import annotations

import sys

from src.governance.model_inventory import (add_collection_item, list_models,
                                            rebuild_inventory_view)

ACTOR = "backfill_version_register"
VERSIONS = "version_history"
CHANGES = "change_history"


def gaps(config=None) -> list[dict]:
    """Every version a model's change history records but its register does not.

    Ordered by model, then by the change history's own order, so the rows are added
    in the sequence the changes were recorded rather than an arbitrary one.
    """
    found = []
    for model in list_models(config=config, include_retired=True):
        data = model.get("data") or {}
        registered = {v.get("version") for v in (data.get(VERSIONS) or [])}
        for change in data.get(CHANGES) or []:
            version = (change.get("version") or "").strip()
            if not version or version in registered:
                continue
            registered.add(version)          # a change history repeating a version adds one row
            found.append({
                "model_id": model["model_id"],
                "version": version,
                "date": change.get("date") or "",
                "description": change.get("description") or "",
                "author": change.get("author") or "",
            })
    return found


def unfillable(config=None) -> list[dict]:
    """Models whose CURRENT version is in neither register — nothing to derive from.

    Reported rather than fixed: inventing a date and a description for a release
    nobody recorded would put a fiction in the timeline, which is worse than a gap
    somebody can see.
    """
    out = []
    for model in list_models(config=config, include_retired=True):
        data = model.get("data") or {}
        current = (data.get("version") or "").strip()
        if not current:
            continue
        known = {v.get("version") for v in (data.get(VERSIONS) or [])}
        known |= {c.get("version") for c in (data.get(CHANGES) or [])}
        if current not in known:
            out.append({"model_id": model["model_id"], "version": current})
    return out


def backfill(*, actor: str = ACTOR, apply: bool = False, config=None) -> dict:
    """Add the derivable rows. Returns a summary; writes only when ``apply``."""
    rebuild_inventory_view(config=config)
    to_add = gaps(config=config)
    if apply:
        for row in to_add:
            add_collection_item(
                model_id=row["model_id"], collection=VERSIONS, actor=actor,
                reason="Backfill: version recorded in the change history but missing "
                       "from the version register",
                fields={"version": row["version"], "date": row["date"],
                        "description": row["description"], "author": row["author"]},
                config=config,
            )
        rebuild_inventory_view(config=config)
    return {"added": to_add, "unfillable": unfillable(config=config), "applied": apply}


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else list(argv)
    apply = "--apply" in argv
    actor = ACTOR
    if "--actor" in argv:
        actor = argv[argv.index("--actor") + 1]
    result = backfill(actor=actor, apply=apply, config=None)

    for row in result["added"]:
        verb = "added" if apply else "would add"
        print(f"{row['model_id']:14} {verb} {row['version']:8} "
              f"{row['date'] or '(no date)':12} {row['description'][:60]}")
    if not result["added"]:
        print("No version-register gaps: every recorded change has a timeline row.")
    for row in result["unfillable"]:
        print(f"{row['model_id']:14} current version {row['version']} appears in neither "
              "register — nothing to derive it from, so it is left for a human")
    if not apply and result["added"]:
        print("\nNothing written. Re-run with --apply to record these.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
