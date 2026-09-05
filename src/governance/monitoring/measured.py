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
"""What the measures can say about a record, and what they cannot say and why.

The bridge between the observations somebody records and the library that scores them.
Two rules, and the second is the one that matters.

**A measure that cannot be computed says why, in the same shape as one that can.** Not
zero, not blank, not a missing row: "no baseline recorded for this field" is a finding a
monitoring report should print, and it is a different finding from "measured, and the
distribution has not moved". The library already refuses rather than raising; this
carries the refusal through to the page with the reason attached.

**A record with no observations at all reads not evidenced, once.** It does not read as
four measures all failing, which would look like four problems where there is one:
nobody has recorded the data.
"""
from __future__ import annotations

from typing import Any

from config.governance._assessments import MONITORING_COLLECTION
from config.governance._monitoring_measures import (BACKTEST, FIELD_TYPE_CLASSIFICATION,
                                                    PSI, STATUS_NO_DATA)
from src.governance.monitoring.measures import backtest, psi
from src.governance.monitoring.measures._result import no_data


def _numbers(text: Any) -> list[float]:
    """A comma-separated field as numbers, ignoring anything that is not one.

    Transcribed from a monitoring pack by a person, so it arrives with spaces, trailing
    commas and the occasional dash for a bucket nobody filled.
    """
    out = []
    for part in str(text or "").replace(";", ",").split(","):
        part = part.strip()
        if not part:
            continue
        try:
            out.append(float(part))
        except ValueError:
            continue
    return out


def _labels(text: Any, count: int) -> list[str]:
    given = [p.strip() for p in str(text or "").split(",") if p.strip()]
    return given if len(given) == count else [f"bucket {i + 1}" for i in range(count)]


def _expand(labels: list[str], counts: list[float]) -> list[str]:
    """Bucket counts back into a categorical series the index can be computed over.

    The measures take observations; a monitoring pack carries counts. Expanding here
    rather than giving ``psi`` a second signature keeps one implementation of the index
    — the arithmetic a reviewer checks by hand stays the arithmetic that runs.
    """
    series: list[str] = []
    for label, count in zip(labels, counts):
        series.extend([label] * int(max(count, 0)))
    return series


def measure_observation(row: dict[str, Any]) -> list[dict[str, Any]]:
    """Every measure one recorded observation supports, each with its reason if not.

    A row may support one, both or neither: a distribution snapshot gives the stability
    index, predicted-against-realised gives the backtest, and a row carrying only a note
    gives neither and says so.
    """
    field = str(row.get("field") or "").strip() or "this field"
    field_type = str(row.get("field_type") or "").strip() or FIELD_TYPE_CLASSIFICATION
    out = []

    baseline = _numbers(row.get("baseline_counts"))
    current = _numbers(row.get("current_counts"))
    if baseline and current and len(baseline) == len(current):
        labels = _labels(row.get("buckets"), len(baseline))
        out.append({**psi(_expand(labels, baseline), _expand(labels, current),
                          categorical=True), "field": field})
    else:
        missing = ("no baseline and no current distribution recorded"
                   if not baseline and not current else
                   "no baseline distribution recorded" if not baseline else
                   "no current distribution recorded" if not current else
                   "the baseline and current distributions have different bucket counts")
        out.append({**no_data(PSI), "field": field, "detail": missing})

    predicted = _numbers(row.get("predicted"))
    realised = _numbers(row.get("realised"))
    if predicted and realised:
        out.append({**backtest(predicted, realised, field_type), "field": field})
    else:
        out.append({**no_data(BACKTEST), "field": field,
                    "detail": "no predicted and realised values recorded, so nothing "
                              "can be said about whether what it predicted happened"})
    return out


def measured_position(data: dict[str, Any]) -> dict[str, Any]:
    """The record's measured monitoring position.

    ``evidenced`` is the honest headline: False where nobody has recorded an
    observation, which is a different statement from every measure coming back
    unmeasurable — and the one a committee needs first.
    """
    rows = data.get(MONITORING_COLLECTION) or []
    if not rows:
        return {"evidenced": False, "results": [],
                "why": "No monitoring observation has been recorded against this "
                       "record, so no distribution or outcome measure can be reported. "
                       "This is the absence of a measurement, not a measurement of "
                       "no change."}
    results = [result for row in rows for result in measure_observation(row)]
    return {"evidenced": any(r["status"] != STATUS_NO_DATA for r in results),
            "results": results, "why": ""}


__all__ = ["measure_observation", "measured_position"]
