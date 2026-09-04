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
"""Bring an existing estate's Data Source list up to the shipped catalogue.

Expanding ``DEFAULT_DATA_SOURCES`` is not enough on its own. The first-run seed
deliberately seeds a vacuum and never reconciles a curated list, so an estate that
already has data sources -- any estate that has been used -- would never see the
providers added later, and a reviewer would go on choosing between "Manual" and
"Other" while the model actually draws on the Met Office.

Idempotent, and it never overrules a curator:

- An entry whose value already exists is left alone, matched case- and
  whitespace-insensitively so "met office" is not added beside "Met Office".
- Nothing is removed and nothing is reordered.

**It reconciles; the first-run seed does not.** That is the one real difference between
this and ``ensure_default_reference_lists``, and it is worth being plain about: a
reference list carries no record of a removal, so this cannot tell "never had it" from
"deleted it on purpose", and running it a second time after somebody has trimmed the
list WILL put back what they removed. That is acceptable because it is run deliberately,
once, by an operator who wants the catalogue -- and unacceptable as anything automatic,
which is why it is a script and not a startup hook.
- ``kind`` is filled on an existing row only where it is BLANK and the catalogue
  knows the answer. A blank is an absence, not a decision, and leaving "Simulated"
  unclassified beside twenty rows marked External reads as an oversight. A kind
  somebody has actually set is never overwritten, even to disagree with it.

An empty list is left to the first-run seed, which now ships the full catalogue.

Run against the configured ModelRisk database:

    python -m scripts.backfill_data_sources
"""
from __future__ import annotations

from config.governance import DATA_SOURCE_LIST, DEFAULT_DATA_SOURCES
from src.governance.reference import add_option, get_reference_lists, update_option

ACTOR = "backfill_data_sources"
_REASON = "Extend the data-source catalogue to the shipped set"


def _key(value: str) -> str:
    """The form two entries are compared on: an entry is a name, not a spelling."""
    return " ".join(str(value or "").split()).casefold()


def _fill_blank_kinds(rows: list[dict], catalogue: dict[str, str], config) -> list[str]:
    """Set ``kind`` on existing rows that have none and that the catalogue knows."""
    filled = []
    for row in rows:
        if (row.get("kind") or "").strip():
            continue
        kind = catalogue.get(_key(row.get("value")))
        if not kind:
            continue
        update_option(list_name=DATA_SOURCE_LIST, item_id=row["item_id"],
                      fields={"kind": kind}, actor=ACTOR,
                      reason="Record whether the feed originates outside the firm",
                      config=config)
        filled.append(f"{row.get('value')} ({kind})")
    return filled


def backfill_data_sources(config=None) -> str:
    """Add every shipped data source the list does not already carry."""
    rows = get_reference_lists(config=config).get(DATA_SOURCE_LIST) or []
    if not rows:
        return "list empty — the first-run seed will supply the full catalogue"

    catalogue = {_key(e["value"]): e["kind"] for e in DEFAULT_DATA_SOURCES}
    present = {_key(row.get("value")) for row in rows}
    missing = [entry for entry in DEFAULT_DATA_SOURCES
               if _key(entry["value"]) not in present]

    for entry in missing:
        add_option(list_name=DATA_SOURCE_LIST, fields=dict(entry), actor=ACTOR,
                   reason=_REASON, config=config)
    filled = _fill_blank_kinds(rows, catalogue, config)

    if not missing and not filled:
        return f"nothing to do — all {len(DEFAULT_DATA_SOURCES)} present and classified"
    parts = []
    if missing:
        parts.append(f"added {len(missing)} of {len(DEFAULT_DATA_SOURCES)}: "
                     + ", ".join(e["value"] for e in missing))
    if filled:
        parts.append("classified " + ", ".join(filled))
    return "; ".join(parts)


def main() -> None:
    # No read-model rebuild afterwards: reference lists are collections on the
    # reference aggregate and are read through ``get_reference_lists``, not through a
    # projected view. Every other backfill in this directory does need one.
    print(backfill_data_sources())


if __name__ == "__main__":
    main()
