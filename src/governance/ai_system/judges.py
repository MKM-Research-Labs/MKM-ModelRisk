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
"""The judge as a dependency: which records a judge's scores feed.

A judge is a model, and a change to it — a version bump, a re-prompted rubric, a
swapped provider — is a Measurement-class change that invalidates the scores it
produced. That only means anything if the records depending on it can be found, so this
answers the question the change register asks when a judge moves: what else does this
affect?

Derived from the evaluations rather than declared separately. An evaluation naming its
judge IS the dependency; a second register of judge relationships would be a second
answer, and the two would disagree the first time somebody recorded an evaluation
without updating it.
"""
from __future__ import annotations

from typing import Any

from config.governance._assessments import EVALUATIONS_COLLECTION

JUDGE_FIELD = "judge_ai_system_id"


def judges_of(data: dict[str, Any]) -> list[str]:
    """The judges whose scores this record relies on, in the order first named."""
    seen: list[str] = []
    # A calibration names its judge as surely as an evaluation does: a judge whose
    # agreement with the experts is on record is one this system relies on.
    rows = list(data.get(EVALUATIONS_COLLECTION) or []) + list(
        data.get("judge_calibrations") or [])
    for row in rows:
        judge = str(row.get(JUDGE_FIELD) or "").strip()
        if judge and judge not in seen:
            seen.append(judge)
    return seen


def dependents_of(judge_id: str, records: list[dict[str, Any]],
                  id_key: str) -> list[str]:
    """Every record whose evaluations name this judge.

    ``records`` are read-model rows and ``id_key`` names their id field, so one
    implementation serves models, ML Applications and AI Systems — a judge scores
    whatever it is pointed at, and its dependents are not all one record type.
    """
    return [row[id_key] for row in records
            if judge_id in judges_of(row.get("data") or {})]


def affected_by_judge_change(judge_id: str, estate: dict[str, list]) -> list[dict[str, str]]:
    """The affected-artifacts list for a change to this judge.

    ``estate`` maps a record type's id field to its rows. Returned as records rather
    than ids so a change proposal can name what it affects without a second lookup —
    the point being that a judge change surfaces on every dependent instead of having
    to be discovered.
    """
    affected = []
    for id_key, rows in estate.items():
        for record_id in dependents_of(judge_id, rows, id_key):
            affected.append({"record_type": id_key, "record_id": record_id})
    return affected


__all__ = ["JUDGE_FIELD", "affected_by_judge_change", "dependents_of", "judges_of"]
