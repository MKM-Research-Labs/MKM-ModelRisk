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
"""Backfill: file existing records under the functional groups somebody has chosen.

Every other backfill in here DERIVES what it writes. This one cannot, and that is
the point: a functional group says what a record is FOR, and nothing already on a
record answers that. Type says what it IS, the name is a name, and guessing from
either would put somebody's filing decision into the governance record under the
platform's authority rather than theirs.

So this takes a mapping you supply and does exactly what it says, reporting
everything it will not touch:

    record_id,group
    MKM-SG-001,Storm Generation
    PRD-PRS,Instrument Pricer

``group`` is the group's NAME as its division ratified it -- a group id (FG-002)
works too, for anyone reading them off the Admin screen. Names are matched
case-insensitively and are resolved against the division of THAT record, because
ids and names are per division: two divisions may both have a "Pricing".

    python -m scripts.backfill_functional_groups groups.csv           # show the plan
    python -m scripts.backfill_functional_groups groups.csv --apply   # file them
    python -m scripts.backfill_functional_groups groups.csv --refile  # move filed ones too

Idempotent: a record already filed under the group the mapping names is left alone,
so re-running writes nothing. A record already filed under a DIFFERENT group is
reported and skipped unless ``--refile`` is given -- a backfill should not quietly
overturn a decision somebody made on the screen.

Covers all four registers. Rebuilds the read models of the ones it touched, because
a backfill driven from a script leaves them stale otherwise.
"""
from __future__ import annotations

import csv
import sys

from config.governance import FUNCTIONAL_GROUP_FIELD
from src.governance.ai_system import (list_ai_systems, rebuild_ai_system_view,
                                      update_ai_system_field)
from src.governance.errors import DomainError
from src.governance.functional_groups import get_functional_groups
from src.governance.ml_application import (list_ml_applications,
                                           rebuild_ml_application_view,
                                           update_ml_application_field)
from src.governance.model_inventory import (list_models, rebuild_inventory_view,
                                            update_model_field)
from src.governance.product import (list_products, rebuild_product_view,
                                    update_product_field)

ACTOR = "backfill_functional_groups"
REASON = "Backfill: filed under the functional group its division agreed"

# One row per register: what it holds, how a record is named, how a field is set on it,
# and how its read model is rebuilt. Held as data so nothing below branches on which
# register a record came from.
REGISTERS = (
    ("model", list_models, "model_id",
     lambda rid, **kw: update_model_field(model_id=rid, **kw), rebuild_inventory_view),
    ("Product", list_products, "product_id",
     lambda rid, **kw: update_product_field(product_id=rid, **kw), rebuild_product_view),
    ("ML Application", list_ml_applications, "ml_application_id",
     lambda rid, **kw: update_ml_application_field(ml_application_id=rid, **kw),
     rebuild_ml_application_view),
    ("AI System", list_ai_systems, "ai_system_id",
     lambda rid, **kw: update_ai_system_field(ai_system_id=rid, **kw),
     rebuild_ai_system_view),
)


def load_mapping(path: str) -> list[tuple[str, str]]:
    """``[(record id, group)]`` from a two-column CSV, header optional.

    Order is kept, so the report reads in the order somebody wrote the file rather
    than in an order the machine chose.
    """
    rows: list[tuple[str, str]] = []
    with open(path, newline="", encoding="utf-8") as handle:
        for row in csv.reader(handle):
            if len(row) < 2:
                continue
            record_id, group = row[0].strip(), row[1].strip()
            if not record_id or record_id.lower() in ("record_id", "id"):
                continue
            rows.append((record_id, group))
    return rows


def _estate(config=None) -> dict[str, dict]:
    """Every live record, by id, with what this script needs to decide about it."""
    found: dict[str, dict] = {}
    for noun, lister, id_key, setter, _rebuild in REGISTERS:
        for row in lister(config=config):
            if row.get("retired"):
                continue
            data = row.get("data") or {}
            found[str(row[id_key])] = {
                "id": str(row[id_key]), "noun": noun, "setter": setter,
                "division": data.get("division") or "",
                "current": str(data.get(FUNCTIONAL_GROUP_FIELD) or "").strip(),
            }
    return found


def _resolve(group: str, division: str, config=None) -> str | None:
    """The group id ``group`` names in ``division``, by id or by name."""
    ratified = get_functional_groups(division, config)
    for entry in ratified:
        if entry.get("id") == group:
            return entry["id"]
    for entry in ratified:
        if (entry.get("name") or "").strip().casefold() == group.casefold():
            return entry["id"]
    return None


def plan(mapping, config=None) -> list[dict]:
    """What each row of the mapping would do, without doing any of it.

    Every row comes back with a verdict, including the ones that will be skipped:
    a backfill you cannot read the refusals of is one you have to run to understand.
    """
    estate = _estate(config)
    out = []
    for record_id, group in mapping:
        record = estate.get(record_id)
        if record is None:
            out.append({"id": record_id, "group": group, "verdict": "unknown",
                        "detail": "no live record with this id"})
            continue
        entry = dict(record, group=group)
        if not get_functional_groups(record["division"], config):
            out.append(dict(entry, verdict="no-groups",
                            detail=f"{record['division'] or 'its division'} has ratified "
                                   "no functional groups"))
            continue
        group_id = _resolve(group, record["division"], config)
        if group_id is None:
            out.append(dict(entry, verdict="no-such-group",
                            detail=f"{record['division']} has no group called '{group}'"))
            continue
        entry["group_id"] = group_id
        if record["current"] == group_id:
            out.append(dict(entry, verdict="already", detail="already filed here"))
        elif record["current"]:
            out.append(dict(entry, verdict="filed-elsewhere",
                            detail=f"currently {record['current']}"))
        else:
            out.append(dict(entry, verdict="file", detail=""))
    return out


def backfill(mapping, *, actor: str = ACTOR, apply: bool = False,
             refile: bool = False, config=None) -> list[dict]:
    """Apply the plan. Writes only when ``apply``; returns the plan either way."""
    rows = plan(mapping, config)
    writable = [r for r in rows
                if r["verdict"] == "file" or (refile and r["verdict"] == "filed-elsewhere")]
    if not apply:
        return rows
    touched = set()
    for row in writable:
        try:
            row["setter"](row["id"], field=FUNCTIONAL_GROUP_FIELD, value=row["group_id"],
                          actor=actor, reason=REASON, config=config)
            touched.add(row["noun"])
        except DomainError as exc:
            row["verdict"] = "refused"
            row["detail"] = str(exc)
    # The read models are stale until they are rebuilt, and a backfill that leaves them
    # so is how the estate comes to disagree with its own event log.
    for noun, _lister, _id_key, _setter, rebuild in REGISTERS:
        if noun in touched:
            rebuild(config=config)
    return rows


_ORDER = ("file", "filed-elsewhere", "refused", "no-such-group", "no-groups",
          "already", "unknown")


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else list(argv)
    paths = [a for a in argv if not a.startswith("--")]
    if not paths:
        print(__doc__)
        return 2
    apply = "--apply" in argv
    refile = "--refile" in argv
    actor = argv[argv.index("--actor") + 1] if "--actor" in argv else ACTOR

    rows = backfill(load_mapping(paths[0]), actor=actor, apply=apply, refile=refile)
    verb = {"file": "filed" if apply else "would file",
            "filed-elsewhere": "refiled" if (apply and refile) else "SKIPPED"}
    for verdict in _ORDER:
        for row in [r for r in rows if r["verdict"] == verdict]:
            what = verb.get(verdict, verdict.upper())
            name = f"{row.get('group', '')} ({row.get('group_id', '?')})"
            print(f"{row['id']:16} {row.get('noun', ''):15} {what:12} {name:38} "
                  f"{row['detail']}")
    counts = {v: len([r for r in rows if r["verdict"] == v]) for v in _ORDER}
    print("\n" + " · ".join(f"{v}: {n}" for v, n in counts.items() if n))
    if not apply and counts.get("file"):
        print("Nothing written. Re-run with --apply to file these.")
    if counts.get("filed-elsewhere") and not refile:
        print("Records already filed elsewhere were left alone; --refile moves them.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
