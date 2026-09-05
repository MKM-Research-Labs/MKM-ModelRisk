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
"""Distribution monitoring: has the population moved, and did it move as a whole?

Two questions that look alike and are not. The population stability index asks whether
the SHAPE of a distribution has changed -- run over the same field this month and last,
it says the mix moved -- and it says nothing about which individuals moved. A transition
matrix asks exactly that: it needs the same subjects observed twice, and it separates
"a third of the book moved up a grade" from "a third moved up and a third moved down",
which have identical marginal distributions and could not be more different.

Written in plain Python with no numerical dependency, deliberately. A reviewer
challenging a monitoring figure has to be able to follow the arithmetic, and the tests
compute their expected values by hand for the same reason.
"""
from __future__ import annotations

import math
from collections import Counter
from typing import Any, Iterable, Sequence

from config.governance._monitoring_measures import (PSI, PSI_BINS, PSI_ZERO_FLOOR,
                                                    STATUS_OK, TRANSITION_STABILITY)
from src.governance.monitoring.measures._result import (enough, no_data, result,
                                                        too_few, undefined)


def _numeric(values: Iterable[Any]) -> list[float]:
    """The values that are actually numbers. A field monitored as continuous may still
    carry a blank or a sentinel, and dropping those is honest where coercing is not."""
    out = []
    for v in values:
        if v is None or isinstance(v, bool):
            continue
        try:
            out.append(float(v))
        except (TypeError, ValueError):
            continue
    return out


def quantile_edges(values: Sequence[float], bins: int = PSI_BINS) -> list[float]:
    """Cut points at equal quantiles of ``values``, duplicates removed.

    Taken from the EXPECTED distribution and then applied to both, which is the whole
    point: bins recut on each period would compare two different rulers and report
    stability whatever happened.
    """
    ordered = sorted(values)
    if not ordered:
        return []
    edges = []
    for i in range(1, bins):
        position = (len(ordered) - 1) * i / bins
        low = int(math.floor(position))
        high = min(low + 1, len(ordered) - 1)
        edges.append(ordered[low] + (ordered[high] - ordered[low]) * (position - low))
    # Ties collapse the bins they span; a field where half the rows share one value
    # genuinely has fewer than ``bins`` distinguishable buckets.
    return sorted(set(edges))


def _bucket(value: float, edges: Sequence[float]) -> int:
    for i, edge in enumerate(edges):
        if value < edge:
            return i
    return len(edges)


def _shares(counts: Sequence[int], total: int) -> list[float]:
    """Counts as shares, with empty buckets floored so the logarithm stays finite."""
    return [max(c / total, PSI_ZERO_FLOOR) if total else PSI_ZERO_FLOOR for c in counts]


def psi(expected: Iterable[Any], actual: Iterable[Any], *,
        bins: int = PSI_BINS, categorical: bool = False) -> dict[str, Any]:
    """Population stability index between a baseline and a current sample.

    Sum over buckets of ``(actual share - expected share) * ln(actual / expected)``.
    Symmetric by construction and zero only when the two distributions are identical
    bucket for bucket.

    ``n`` is the CURRENT sample: the baseline is a fixed reference and its size is not
    what makes this period's reading trustworthy.
    """
    if categorical:
        exp_raw = [v for v in expected if v is not None]
        act_raw = [v for v in actual if v is not None]
        keys = sorted({str(v) for v in exp_raw} | {str(v) for v in act_raw})
        exp_counts = Counter(str(v) for v in exp_raw)
        act_counts = Counter(str(v) for v in act_raw)
        exp_n, act_n = len(exp_raw), len(act_raw)
        labels = keys
        exp_buckets = [exp_counts[k] for k in keys]
        act_buckets = [act_counts[k] for k in keys]
    else:
        exp_values, act_values = _numeric(expected), _numeric(actual)
        exp_n, act_n = len(exp_values), len(act_values)
        if not exp_n or not act_n:
            return no_data(PSI)
        # A baseline with one distinct value has no distribution to compare against.
        # It still yields cut points — every quantile of a constant is that constant —
        # so guarding on the EDGES being empty misses it, and what comes back is not a
        # stability index at all but "what fraction now sits below that value".
        if len(set(exp_values)) < 2:
            return undefined(PSI, act_n, "the baseline holds a single value, so it has "
                                         "no distribution to compare against")
        edges = quantile_edges(exp_values, bins)
        if not edges:  # pragma: no cover - unreachable once the baseline varies
            return undefined(PSI, act_n, "the baseline has no quantile cut points")
        labels = [f"bucket {i}" for i in range(len(edges) + 1)]
        exp_buckets = [0] * (len(edges) + 1)
        act_buckets = [0] * (len(edges) + 1)
        for v in exp_values:
            exp_buckets[_bucket(v, edges)] += 1
        for v in act_values:
            act_buckets[_bucket(v, edges)] += 1

    if not exp_n or not act_n:
        return no_data(PSI)
    if not enough(PSI, act_n):
        return too_few(PSI, act_n)

    exp_shares = _shares(exp_buckets, exp_n)
    act_shares = _shares(act_buckets, act_n)
    total = sum((a - e) * math.log(a / e) for e, a in zip(exp_shares, act_shares))
    return result(PSI, total, n=act_n, status=STATUS_OK,
                  detail={"buckets": [
                      {"bucket": label, "expected": e, "actual": a}
                      for label, e, a in zip(labels, exp_shares, act_shares)]})


def transition_matrix(previous: Iterable[Any], current: Iterable[Any]) -> dict[str, Any]:
    """Counts of moves from each previous state to each current state.

    The two sequences are PAIRED -- element i of each is the same subject observed
    twice -- so a pair with either side missing is dropped rather than aligned against
    somebody else's row.
    """
    pairs = [(str(p), str(c)) for p, c in zip(previous, current)
             if p is not None and c is not None]
    states = sorted({p for p, _ in pairs} | {c for _, c in pairs})
    counts = Counter(pairs)
    return {
        "states": states,
        "rows": {frm: {to: counts[(frm, to)] for to in states} for frm in states},
        "n": len(pairs),
    }


def stability(matrix: dict[str, Any]) -> dict[str, Any]:
    """The share of paired subjects that ended where they started -- the diagonal.

    One number over the whole matrix, because that is what a RAG needs. Where the
    movement went is in the matrix itself, and a report that shows only this has thrown
    away the interesting half.
    """
    n = matrix.get("n", 0)
    if not n:
        return no_data(TRANSITION_STABILITY)
    if not enough(TRANSITION_STABILITY, n):
        return too_few(TRANSITION_STABILITY, n)
    rows = matrix.get("rows") or {}
    stayed = sum(rows.get(state, {}).get(state, 0) for state in matrix.get("states", []))
    return result(TRANSITION_STABILITY, stayed / n, n=n, status=STATUS_OK,
                  detail={"stayed": stayed, "moved": n - stayed})


__all__ = ["psi", "quantile_edges", "stability", "transition_matrix"]
