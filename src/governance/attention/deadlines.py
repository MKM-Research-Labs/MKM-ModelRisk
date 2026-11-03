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
"""When each completeness finding falls due, and how far past it is (pure).

The audit carries each gap's band deadline (``sla_days``) and the finding history
carries how long the gap has been open; neither says WHEN it was due. That date is
what an owner asks for first, and a dashboard that only answers "late, yes or no"
sends them to the database to find it. This works it out once, for the dashboard
row and the record's own Remediation stage alike, so the two cannot quote different
dates for the same finding.

The clock is the history's: a finding's first-seen date is the first day the daily
observation saw it, not the day the field went blank. A finding the observation has
not seen yet has no date at all, and is reported as unobserved rather than given one.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from config.governance import COMING_DUE_DAYS, FINDING_DEADLINE_LABELS
from src.governance.attention._rules import finding_key

OVERDUE = "overdue"
DUE_SOON = "due_soon"
OPEN = "open"
UNOBSERVED = "unobserved"
_ORDER = {OVERDUE: 0, DUE_SOON: 1, OPEN: 2, UNOBSERVED: 3}


def _status(days_over: int | None) -> str:
    if days_over is None:
        return UNOBSERVED
    if days_over > 0:
        return OVERDUE
    return DUE_SOON if -days_over <= COMING_DUE_DAYS else OPEN


def gap_deadlines(gaps, ages: dict | None, as_of: str) -> list[dict[str, Any]]:
    """Every gap with its first-seen date, due date and days over, worst first.

    Days over is negative while a finding is still inside its deadline. Past is
    strictly past, as in ``past_sla``: a finding due today is not yet late.
    """
    today = date.fromisoformat(as_of)
    out = []
    for gap in gaps or []:
        age = (ages or {}).get(finding_key(gap))
        sla = gap.get("sla_days")
        first_seen = due = days_over = None
        if age is not None and sla is not None:
            first = today - timedelta(days=age)
            first_seen = first.isoformat()
            due = (first + timedelta(days=sla)).isoformat()
            days_over = age - sla
        status = _status(days_over)
        out.append({
            "key": gap.get("key"), "label": gap.get("label"), "band": gap.get("band"),
            "action": gap.get("action"), "sla_days": sla, "first_seen": first_seen,
            "due": due, "days_over": days_over, "status": status,
            "status_label": FINDING_DEADLINE_LABELS[status],
        })
    out.sort(key=lambda g: (_ORDER[g["status"]], -(g["days_over"] or 0),
                            g["due"] or "", g["label"] or ""))
    return out


def overdue_summary(gaps, ages: dict | None, as_of: str) -> dict[str, Any]:
    """What a record's past-deadline row says: the earliest due date among its late
    findings, the furthest any of them is over, and which they are."""
    late = [g for g in gap_deadlines(gaps, ages, as_of) if g["status"] == OVERDUE]
    if not late:
        return {"due": None, "days_over": None, "detail": ""}
    return {
        "due": min(g["due"] for g in late),
        "days_over": max(g["days_over"] for g in late),
        "detail": "Overdue: " + ", ".join(
            f"{g['label']} (due {g['due']})" for g in late),
    }
