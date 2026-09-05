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
"""Backtesting: how did what it predicted compare with what happened?

Dispatched on the FIELD TYPE, not on the record type. A classifier's output is scored
with accuracy, precision, recall and F1; a continuous prediction with RMSE, MAE, R² and
bias. Half this estate is regression -- depth-damage curves, floor levels, storm
intensities -- and a monitoring pack that reports AUC for those is one nobody reads
twice, which is why the metric list is config and this module only knows how to compute
what it is asked for.

Bias is carried alongside the error metrics because it answers a different question:
RMSE says how wrong, bias says which way. A model that is consistently 8% low is a
model somebody can correct, and an error metric alone hides that.
"""
from __future__ import annotations

import math
from typing import Any, Iterable

from config.governance._monitoring_measures import (BACKTEST, BACKTEST_HEADLINE,
                                                    BACKTEST_METRICS,
                                                    FIELD_TYPE_CLASSIFICATION,
                                                    FIELD_TYPE_REGRESSION, STATUS_OK)
from src.governance.monitoring.measures._result import (enough, no_data, result,
                                                        too_few, undefined)


def _pairs(predicted: Iterable[Any], realised: Iterable[Any]) -> list[tuple]:
    """Paired observations with neither side missing. Element i of each is the same
    subject, so an unpaired value is dropped rather than shifted onto its neighbour."""
    return [(p, r) for p, r in zip(predicted, realised) if p is not None and r is not None]


def _numeric_pairs(pairs: list[tuple]) -> list[tuple[float, float]]:
    out = []
    for p, r in pairs:
        try:
            out.append((float(p), float(r)))
        except (TypeError, ValueError):
            continue
    return out


def _classification(pairs: list[tuple]) -> dict[str, float]:
    """Accuracy over all classes; precision, recall and F1 averaged over the classes
    present, so a rare class counts as much as a common one.

    Macro-averaged rather than weighted on purpose: the question a model risk function
    asks is whether the model works for the small groups too, and a weighted average is
    designed to let the majority class answer for them.
    """
    labels = sorted({str(r) for _, r in pairs} | {str(p) for p, _ in pairs})
    correct = sum(1 for p, r in pairs if str(p) == str(r))
    precisions, recalls, f1s = [], [], []
    for label in labels:
        tp = sum(1 for p, r in pairs if str(p) == label and str(r) == label)
        predicted_positive = sum(1 for p, _ in pairs if str(p) == label)
        actual_positive = sum(1 for _, r in pairs if str(r) == label)
        precision = tp / predicted_positive if predicted_positive else 0.0
        recall = tp / actual_positive if actual_positive else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
        precisions.append(precision)
        recalls.append(recall)
        f1s.append(f1)
    n_labels = len(labels) or 1
    return {
        "accuracy": correct / len(pairs),
        "precision": sum(precisions) / n_labels,
        "recall": sum(recalls) / n_labels,
        "f1": sum(f1s) / n_labels,
    }


def _regression(pairs: list[tuple[float, float]]) -> dict[str, float] | None:
    """RMSE, MAE, R² and mean bias. ``None`` where R² has no meaning."""
    n = len(pairs)
    errors = [p - r for p, r in pairs]
    mean_realised = sum(r for _, r in pairs) / n
    ss_total = sum((r - mean_realised) ** 2 for _, r in pairs)
    if ss_total == 0:
        # Every realised value identical: R² divides by zero, and "explains none of the
        # variance" is not a fair reading when there was no variance to explain.
        return None
    ss_residual = sum(e ** 2 for e in errors)
    return {
        "rmse": math.sqrt(ss_residual / n),
        "mae": sum(abs(e) for e in errors) / n,
        "r2": 1 - (ss_residual / ss_total),
        "bias": sum(errors) / n,
    }


def backtest(predicted: Iterable[Any], realised: Iterable[Any],
             field_type: str = FIELD_TYPE_CLASSIFICATION) -> dict[str, Any]:
    """Score predictions against what actually happened.

    The headline metric named in config carries the rating; every metric configured for
    the field type is returned in ``detail``, because a committee shown one number will
    ask what the others were.
    """
    if field_type not in BACKTEST_METRICS:
        raise ValueError(f"unknown field type for backtesting: {field_type}")
    pairs = _pairs(predicted, realised)
    if not pairs:
        return no_data(BACKTEST, field_type=field_type)
    if not enough(BACKTEST, len(pairs)):
        return too_few(BACKTEST, len(pairs), field_type=field_type)

    if field_type == FIELD_TYPE_REGRESSION:
        numeric = _numeric_pairs(pairs)
        if not numeric:
            return undefined(BACKTEST, len(pairs), "no numeric pairs",
                             field_type=field_type)
        metrics = _regression(numeric)
        if metrics is None:
            return undefined(BACKTEST, len(numeric),
                             "every realised value is identical, so R² is undefined",
                             field_type=field_type)
        n = len(numeric)
    else:
        metrics = _classification(pairs)
        n = len(pairs)

    wanted = BACKTEST_METRICS[field_type]
    headline = BACKTEST_HEADLINE[field_type]
    return result(BACKTEST, metrics[headline], n=n, status=STATUS_OK,
                  field_type=field_type,
                  detail={"headline": headline,
                          "metrics": {k: metrics[k] for k in wanted}})


__all__ = ["backtest"]
