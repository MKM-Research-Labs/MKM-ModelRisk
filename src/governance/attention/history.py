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
"""Remembering what the audit found, so a finding can be aged and a trend drawn.

The completeness audit is computed fresh every run and keeps no memory, so "how
long has this been open?" is unanswerable from it — which is why the dashboard's
first version left every completeness finding with its owner rather than calling it
late. Inventing an age would have been worse than not having one.

This is the memory. Once a day something looks at the finding set and writes down
what it saw: when each finding was first observed, when it was last observed, and
when it stopped appearing. From those three dates come a finding's age, the
opened-versus-closed counts, and the trend an executive actually asks for after
"do I need to respond?" — namely "is this getting better?".

**What is stored is an observation, not a decision.** Nothing here belongs in the
event log: no committee resolved that a field was blank on a Tuesday. Two ordinary
tables hold it (see ``0012_attention_history.sql``), written through
``replace_view`` — the sanctioned data-write helper — so no SQL is authored outside
``src/database`` (rule R6).

Merge-in-memory rather than upsert-in-SQL is deliberate. The history holds one row
per distinct finding, not one per finding per day, so it grows at the speed of the
estate's problems rather than the calendar; a whole-table rewrite inside one
transaction stays cheap and keeps the write path to helpers that already exist.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from config.history import CLOSED_FINDING_RETENTION_DAYS, TREND_DAYS
from src.database import read_view, replace_view
from src.governance.attention._rules import finding_key

FINDINGS = "finding_history"
FINDING_COLUMNS = ("finding_key", "data", "first_seen", "last_seen", "closed_at")
TREND = "attention_trend"
TREND_COLUMNS = ("as_of", "data")


def _iso(value: Any) -> str:
    """A stored date as an ISO string, whichever way the driver returned it."""
    return value.isoformat() if hasattr(value, "isoformat") else str(value or "")


def _open_findings(audit_rows: list[dict]) -> dict[str, dict]:
    """Every gap the audit is reporting right now, keyed as the history keys it."""
    found = {}
    for row in audit_rows:
        for gap in row.get("gaps") or []:
            found[finding_key(gap)] = {
                "entity_kind": gap.get("entity_kind"),
                "entity_id": gap.get("entity_id"),
                "entity_name": gap.get("entity_name"),
                "key": gap.get("key"),
                "label": gap.get("label"),
                "band": gap.get("band"),
                "severity": gap.get("severity"),
                "sla_days": gap.get("sla_days"),
            }
    return found


def observe(as_of: str, audit_rows: list[dict], totals: dict, config=None) -> dict:
    """Record what is open today, and today's totals. Idempotent within a day.

    Running twice on the same date changes nothing but ``last_seen`` and the day's
    totals row, so a restart cannot double-count and a missed day simply leaves a
    gap in the series rather than corrupting it.
    """
    return {
        "findings": _observe_findings(as_of, audit_rows, config),
        "trend": _observe_totals(as_of, totals, config),
    }


def _observe_findings(as_of: str, audit_rows: list[dict], config=None) -> dict:
    open_now = _open_findings(audit_rows)
    held = {r["finding_key"]: r for r in read_view(FINDINGS, FINDING_COLUMNS, config=config)}
    cutoff = _iso(date.fromisoformat(as_of) - timedelta(days=CLOSED_FINDING_RETENTION_DAYS))

    rows, opened, closed = [], 0, 0
    for key, data in open_now.items():
        previous = held.get(key)
        if previous is None:
            opened += 1
            rows.append((key, data, as_of, as_of, None))
            continue
        # A finding that closed and came back keeps its ORIGINAL first_seen. It is
        # the same hole in the same record, and restarting its clock would let a
        # record escape an SLA by being fixed briefly.
        rows.append((key, data, _iso(previous["first_seen"]), as_of, None))
    for key, previous in held.items():
        if key in open_now:
            continue
        closed_at = _iso(previous["closed_at"]) or as_of
        if closed_at < cutoff:
            continue                     # long settled; let it fall off the history
        if not previous["closed_at"]:
            closed += 1
        rows.append((key, previous["data"], _iso(previous["first_seen"]),
                     _iso(previous["last_seen"]), closed_at))

    replace_view(FINDINGS, FINDING_COLUMNS, rows, config=config)
    return {"open": len(open_now), "opened": opened, "closed": closed,
            "carried": len(rows)}


def _observe_totals(as_of: str, totals: dict, config=None) -> dict:
    held = {_iso(r["as_of"]): r["data"]
            for r in read_view(TREND, TREND_COLUMNS, config=config)}
    held[as_of] = dict(totals)
    keep = _iso(date.fromisoformat(as_of) - timedelta(days=TREND_DAYS))
    rows = sorted((day, data) for day, data in held.items() if day >= keep)
    replace_view(TREND, TREND_COLUMNS, rows, config=config)
    return {"days": len(rows)}


def ages(as_of: str, config=None) -> dict[str, int]:
    """How many days each currently-open finding has been open.

    Absent from the map means never observed — a finding raised since the last
    observation. Those are reported as open rather than as aged, because "we have
    not looked yet" is not "it is new", and only one of those is a claim.
    """
    today = date.fromisoformat(as_of)
    result = {}
    for row in read_view(FINDINGS, FINDING_COLUMNS, config=config):
        if row["closed_at"]:
            continue
        try:
            result[row["finding_key"]] = (today - date.fromisoformat(
                _iso(row["first_seen"]))).days
        except ValueError:
            continue
    return result


def trend(config=None) -> list[dict[str, Any]] | None:
    """The observed series, oldest first, or ``None`` when nothing has been observed.

    ``None`` rather than an empty list on purpose: a strategic view that cannot tell
    "no history yet" from "flat" would read a new install as a stable one.
    """
    rows = read_view(TREND, TREND_COLUMNS, order_by="as_of", config=config)
    if not rows:
        return None
    return [{"as_of": _iso(r["as_of"]), **(r["data"] or {})} for r in rows]
