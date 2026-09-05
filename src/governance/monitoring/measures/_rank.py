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
"""Rank correlation: does the ordering still hold?

The question behind a score is usually not "is the number right" but "does it still put
the right things at the top". A scorecard whose absolute levels have drifted but whose
ranking is intact is a recalibration; one whose ranking has decayed is a rebuild, and
an error metric alone cannot tell you which you are looking at.

Spearman: Pearson's correlation computed on ranks, ties taking the average of the ranks
they span. Rated on the ABSOLUTE value, because a score that has inverted has not
decayed -- it has broken in a way that reads as strong agreement if you drop the sign.
"""
from __future__ import annotations

from typing import Any, Iterable

from config.governance._monitoring_measures import RANK_CORRELATION, STATUS_OK
from src.governance.monitoring.measures._result import (enough, no_data, result,
                                                        too_few, undefined)


def _ranks(values: list[float]) -> list[float]:
    """Ranks, 1-based, with tied values sharing the average of the ranks they span.

    Ties matter more here than they look: an ordinal field monitored this way is mostly
    ties, and ranking them arbitrarily would manufacture agreement or disagreement out
    of the order the rows happened to arrive in.
    """
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        shared = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[order[k]] = shared
        i = j + 1
    return ranks


def _pearson(xs: list[float], ys: list[float]) -> float | None:
    n = len(xs)
    mean_x, mean_y = sum(xs) / n, sum(ys) / n
    dx = [x - mean_x for x in xs]
    dy = [y - mean_y for y in ys]
    denominator = (sum(d * d for d in dx) ** 0.5) * (sum(d * d for d in dy) ** 0.5)
    if denominator == 0:
        return None
    return sum(a * b for a, b in zip(dx, dy)) / denominator


def rank_correlation(a: Iterable[Any], b: Iterable[Any]) -> dict[str, Any]:
    """Spearman's rho between two paired series."""
    pairs = []
    for x, y in zip(a, b):
        if x is None or y is None:
            continue
        try:
            pairs.append((float(x), float(y)))
        except (TypeError, ValueError):
            continue
    if not pairs:
        return no_data(RANK_CORRELATION)
    if not enough(RANK_CORRELATION, len(pairs)):
        return too_few(RANK_CORRELATION, len(pairs))

    rho = _pearson(_ranks([x for x, _ in pairs]), _ranks([y for _, y in pairs]))
    if rho is None:
        # One side is a single repeated value: it has no ordering, so there is no
        # ordering to agree with. Not a correlation of zero, which would read as
        # "measured, and found unrelated".
        return undefined(RANK_CORRELATION, len(pairs),
                         "one series has no variation, so it has no ranking")
    return result(RANK_CORRELATION, abs(rho), n=len(pairs), status=STATUS_OK,
                  detail={"rho": rho, "inverted": rho < 0})


__all__ = ["rank_correlation"]
