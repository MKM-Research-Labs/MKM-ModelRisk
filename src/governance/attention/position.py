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
"""The estate's position, for the two places model risk lands in an ERM (pure).

The queue answers *"do I need to respond?"*. This module answers the two questions
that follow it, and it is split the way the receiving system is:

``operational``  what an operational-risk function consumes: failures that have
                 actually happened in the rolling window, and the control breaches
                 standing open against the estate.
``direction``    what a strategic view consumes: how much of the estate meets the
                 standard its own divisions set, and which way that is moving.
``estate``       the shape of the thing, so either can be read per unit of
                 exposure rather than as a bare count.

There is deliberately no estate-wide *score* here. The audit reports completeness
per record against each division's own threshold, and averaging those into one
figure would be a new number nobody set, sitting on the front page of a
governance record. What is reported instead is a count ratio — how many records
meet the standard, out of how many audited — which any reader can check against
the register and which no weighting can flatter.
"""
from __future__ import annotations

from typing import Any

from config.governance import EVENTS_WINDOW_DAYS, STATE_ESCALATE
from src.governance.attention._rules import below_standard
from src.governance.attention.summary import breakdown

UNTIERED = "untiered"
UNRATED = "unrated"


def _bucket(values, absent: str) -> dict[str, int]:
    """Count values into named buckets, naming the absent case rather than dropping
    it. A record with no tier is a fact about the estate, and an estate summary
    that silently omits it reports a smaller, tidier firm than exists."""
    counts: dict[str, int] = {}
    for value in values:
        key = absent if value in (None, "") else str(value)
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def estate(records: list[dict]) -> dict[str, Any]:
    """How many records of each kind, tier and rating are on the register."""
    data = [(r.get("data") or {}) for r in records]
    return {
        "total": len(records),
        "by_kind": _bucket((r.get("kind") for r in records), "unknown"),
        "by_tier": _bucket((d.get("tier") for d in data), UNTIERED),
        "by_rating": _bucket((d.get("rag_rating") for d in data), UNRATED),
        "by_division": _bucket((d.get("division") for d in data), "unassigned"),
    }


def operational(audit_rows: list[dict], items: list[dict]) -> dict[str, Any]:
    """The operational-risk feed: what has failed, and what control is not holding.

    ``events_in_window`` is read off the audit row rather than recounted, so the
    number an operational-risk function receives is the same one that escalated
    the finding in the report a committee signed.
    """
    failures = [int(row.get("events_in_window") or 0) for row in audit_rows]
    breaches = [i for i in items if i["state"] == STATE_ESCALATE]
    return {
        "window_days": EVENTS_WINDOW_DAYS,
        "failures_in_window": sum(failures),
        "records_with_failures": sum(1 for count in failures if count),
        "control_breaches": len(breaches),
        "control_breaches_by_reason": breakdown(breaches),
    }


def direction(audit_rows: list[dict], trend=None) -> dict[str, Any]:
    """The strategic feed: how much of the estate meets its own standard.

    ``trend`` is the series of prior ``share_meeting_standard`` values. It is
    ``None`` until the finding snapshot exists (the design's phase four), and
    reported as ``None`` rather than omitted — a strategic view that cannot tell
    "no history yet" from "flat" would read a new install as a stable one.
    """
    audited = len(audit_rows)
    below = sum(1 for row in audit_rows if below_standard(row))
    return {
        "records_audited": audited,
        "records_below_standard": below,
        "records_meeting_standard": audited - below,
        "share_meeting_standard": round((audited - below) / audited, 4) if audited else None,
        "trend": trend,
    }
