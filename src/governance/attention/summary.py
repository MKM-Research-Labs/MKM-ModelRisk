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
"""The verdict, and the rows the queue is drawn as (pure).

The dashboard's headline is one sentence, not a score. A composite index would
immediately raise the question of what it is made of, and the honest answer takes
the rest of the page -- the same argument ``model_inventory.risk`` already makes
about not deriving a second rating beside the one the committee sets.

The sentence is assembled from the reason table's own count labels, so the
headline, the collapsed queue row and the API's breakdown describe one set of
findings in one set of words.
"""
from __future__ import annotations

from typing import Any

from config.governance import (
    ATTENTION_QUEUE_CAP,
    ATTENTION_STATES,
    RESPONSE_STATES,
    STATE_CLEAR,
)
from src.governance.attention import _rules

NOTHING_TO_DO = "Nothing needs your response today."
NOTHING_OPEN = "Nothing is outstanding anywhere on the register."


def breakdown(items: list[dict], states=None) -> list[dict[str, Any]]:
    """How many items of each reason, in the order the states are presented.

    Ordered by state and then by first appearance, which is the queue's own order,
    so the sentence reads in the sequence the reader is about to scan.
    """
    wanted = set(states) if states is not None else None
    counts: dict[str, int] = {}
    for item in items:
        if wanted is not None and item["state"] not in wanted:
            continue
        counts[item["reason"]] = counts.get(item["reason"], 0) + 1
    order = {state: i for i, state in enumerate(ATTENTION_STATES)}
    rows = [{"reason": reason, "state": _rules.state_of(reason), "count": count,
             "label": _rules.count_label(reason, count)}
            for reason, count in counts.items()]
    rows.sort(key=lambda r: (order.get(r["state"], len(order)), -r["count"], r["reason"]))
    return rows


def _sentence(clauses: list[str]) -> str:
    """Join clauses as prose. Serial comma before the final "and": these sentences
    routinely list three counts, and without it the last two read as one."""
    if not clauses:
        return ""
    if len(clauses) == 1:
        return clauses[0]
    if len(clauses) == 2:
        return f"{clauses[0]} and {clauses[1]}"
    return ", ".join(clauses[:-1]) + f", and {clauses[-1]}"


def _worst_state(counts: dict[str, int], among=None) -> str | None:
    """The worst state actually present, worst first. ``None`` when nothing is."""
    allowed = set(among) if among is not None else set(ATTENTION_STATES)
    return next((s for s in ATTENTION_STATES if counts.get(s) and s in allowed), None)


def verdict(items: list[dict]) -> dict[str, Any]:
    """The answer to the question the whole page exists to answer.

    ``response_required`` is the answer; ``state`` is the worst state present among
    the items that require one, so a page with a single breach on it reads as a
    breach rather than averaging out to something milder.
    """
    counts = _rules.tally(items)
    owed = [i for i in items if i["state"] in RESPONSE_STATES]
    resting = [i for i in items if i["state"] not in RESPONSE_STATES]
    worst = _worst_state(counts, RESPONSE_STATES)

    if not owed:
        detail = _sentence([r["label"] for r in breakdown(resting)])
        return {
            "response_required": False,
            "state": _worst_state(counts) or STATE_CLEAR,
            "headline": NOTHING_TO_DO,
            "detail": (f"{detail}, all with named owners and in date."
                       if detail else NOTHING_OPEN),
            "counts": counts,
            "breakdown": breakdown(items),
        }

    total = len(owed)
    noun = "item" if total == 1 else "items"
    resting_detail = _sentence([r["label"] for r in breakdown(resting)])
    return {
        "response_required": True,
        "state": worst,
        "headline": f"{total} {noun} need your response."
                    if total != 1 else "1 item needs your response.",
        "detail": _sentence([r["label"] for r in breakdown(owed)]) + "."
                  + (f" {resting_detail.capitalize()} — with named owners and in date."
                     if resting_detail else ""),
        "counts": counts,
        "breakdown": breakdown(items),
    }


def rows(items: list[dict], cap: int = ATTENTION_QUEUE_CAP) -> dict[str, Any]:
    """The queue as the console draws it: grouped reasons collapsed to one row.

    Collapsing is the whole reason the queue stays readable once a rule bites at
    any tier. Thirty rows saying the same thing would bury the two findings that
    are singular, which is the failure the page exists to avoid.

    Truncation is declared rather than silent: a capped list that says nothing
    about the cap reads as "that is all there is".
    """

    collapsed: list[dict[str, Any]] = []
    seen: dict[tuple, dict[str, Any]] = {}
    held: dict[tuple, list[dict]] = {}
    for item in items:
        reason = item["reason"]
        if not _rules.is_grouped(reason):
            collapsed.append({**item, "grouped": False, "count": 1,
                              "records": 1, "members": [item["id"]]})
            continue
        # A reason may collapse wholly, or per owner — the field is configuration,
        # so a queue that floods for a new reason is a config change, not a patch.
        field = _rules.group_key_field(reason)
        key = (reason, item.get(field) if field else None)
        row = seen.get(key)
        if row is None:
            row = {**item, "id": "group:" + ":".join(str(k) for k in key if k),
                   "grouped": True, "count": 0, "members": [], "records": 0,
                   "entity": None, "due": None, "days_over": None,
                   "owner": item.get("owner", "") if field == "owner" else ""}
            seen[key] = row
            held[key] = []
            collapsed.append(row)
        held[key].append(item)
        row["count"] += 1
        row["members"].append(item["id"])
        row["reason_label"] = _rules.count_label(reason, row["count"])
        # The worst date in the group, so a collapsed row still says how bad it is.
        if item.get("days_over") is not None:
            row["days_over"] = max(row["days_over"] or 0, item["days_over"])
        row["records"] = len({(i.get("entity") or {}).get("id") for i in held[key]
                              if (i.get("entity") or {}).get("id")})

    # A group of one is not a group. Collapsing it would hide the record's name
    # behind a count of 1 — the row would read "1 record is below the standard"
    # and then decline to say which, which is the opposite of the point.
    alone = {id(row): items[0] for row, items in
             ((seen[key], held[key]) for key in seen) if len(items) == 1}
    for index, row in enumerate(collapsed):
        item = alone.get(id(row))
        if item is not None:
            collapsed[index] = {**item, "grouped": False, "count": 1,
                                "records": 1, "members": [item["id"]]}
    return {
        "rows": collapsed[:cap],
        "returned": min(len(collapsed), cap),
        "total_rows": len(collapsed),
        "total_items": len(items),
        "truncated": len(collapsed) > cap,
    }
