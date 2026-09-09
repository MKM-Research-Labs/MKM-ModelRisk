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
"""Export: what every record is filed under, in the form the backfill reads back.

The mirror of ``backfill_functional_groups``. That one takes a mapping somebody
chose and files the estate by it; this one reads the estate back out, so a set of
filing decisions can be moved between instances instead of retyped.

    python -m scripts.export_functional_groups > groups.csv       # the assignments
    python -m scripts.export_functional_groups --groups           # the group list
    python -m scripts.export_functional_groups --division PhysicalRisk

Writes CSV to stdout and everything else to stderr, so a redirect captures the data
and nothing else.

**It emits group NAMES, never ids.** Ids are minted per division, so PhysicalRisk's
``FG-001`` and Analytics' ``FG-001`` are different groups; an export of ids replayed
anywhere else would file records under whatever that number happens to mean there,
and nothing about the result would look wrong. Names are what the backfill resolves
against the receiving division, so names are what survive the journey.

Read-only: it opens no write path and takes no actor.
"""
from __future__ import annotations

import csv
import sys

from config.governance import FUNCTIONAL_GROUP_FIELD
from src.governance.ai_system import list_ai_systems
from src.governance.functional_groups import get_functional_groups
from src.governance.ml_application import list_ml_applications
from src.governance.model_inventory import list_models
from src.governance.product import list_products

# One row per register: what it holds and how a record is named. The write half of
# this pair carries setters and rebuilds too; an export needs neither, and listing
# them here anyway would imply this script could write.
REGISTERS = (
    ("model", list_models, "model_id"),
    ("Product", list_products, "product_id"),
    ("ML Application", list_ml_applications, "ml_application_id"),
    ("AI System", list_ai_systems, "ai_system_id"),
)


def _group_names(division: str, config=None) -> dict[str, str]:
    """``{group id: name}`` for one division's ratified list."""
    return {entry["id"]: entry.get("name") or ""
            for entry in get_functional_groups(division, config)
            if entry.get("id")}


def assignments(division: str | None = None, config=None) -> list[tuple[str, str]]:
    """``[(record id, group name)]`` for every live record that carries a group.

    A record with no group is skipped rather than emitted blank: the backfill reads
    this back, and a blank group there is a row it cannot resolve rather than an
    instruction to clear one. Unfiled records are reported on stderr instead, so the
    gap is visible without becoming data.
    """
    names_by_division: dict[str, dict[str, str]] = {}
    rows: list[tuple[str, str]] = []
    unfiled = 0
    for _noun, lister, id_key in REGISTERS:
        for row in lister(config=config):
            if row.get("retired"):
                continue
            data = row.get("data") or {}
            record_division = str(data.get("division") or "")
            if division and record_division != division:
                continue
            group_id = str(data.get(FUNCTIONAL_GROUP_FIELD) or "").strip()
            if not group_id:
                unfiled += 1
                continue
            if record_division not in names_by_division:
                names_by_division[record_division] = _group_names(record_division, config)
            name = names_by_division[record_division].get(group_id)
            if not name:
                # The record names a group its division no longer ratifies. Emitting
                # the bare id would be a row the backfill cannot resolve either, so
                # say so and leave it out rather than write something misleading.
                print(f"  {row[id_key]}: group {group_id} is not in "
                      f"{record_division or '(no division)'}'s ratified list — skipped",
                      file=sys.stderr)
                continue
            rows.append((str(row[id_key]), name))
    if unfiled:
        print(f"  {unfiled} record(s) carry no functional group — not exported",
              file=sys.stderr)
    return rows


def group_list(division: str, config=None) -> list[tuple[str, str]]:
    """``[(name, description)]`` for one division's ratified groups.

    The receiving instance needs these before any assignment can resolve, so this is
    the half of the handover that has to be replayed first.
    """
    return [(entry.get("name") or "", entry.get("description") or "")
            for entry in get_functional_groups(division, config)]


def _write(header: tuple[str, str], rows) -> None:
    writer = csv.writer(sys.stdout, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "-h" in argv or "--help" in argv:
        print(__doc__)
        return 0
    division = argv[argv.index("--division") + 1] if "--division" in argv else None
    if "--groups" in argv:
        if not division:
            print("--groups needs --division: a group list belongs to one division",
                  file=sys.stderr)
            return 2
        _write(("name", "description"), group_list(division))
        return 0
    _write(("record_id", "group"), assignments(division))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
