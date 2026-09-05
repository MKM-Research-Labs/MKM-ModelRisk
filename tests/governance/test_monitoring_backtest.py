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
"""Backtesting, checked against arithmetic done by hand.

The point the plan is emphatic about: half this estate is regression. A backtest that
reported AUC for a depth-damage curve would be a monitoring pack nobody reads twice, so
which metrics apply is config keyed on the FIELD TYPE, and these tests hold that the
regression path is a first-class one rather than an afterthought behind a classifier.
"""
from __future__ import annotations

import math

import pytest

from config.governance._monitoring_measures import (BACKTEST, BACKTEST_METRICS,
                                                    FIELD_TYPE_CLASSIFICATION,
                                                    FIELD_TYPE_REGRESSION, MIN_SAMPLE,
                                                    STATUS_INSUFFICIENT_SAMPLE,
                                                    STATUS_NO_DATA, STATUS_OK,
                                                    STATUS_UNDEFINED)
from src.governance.monitoring.measures import backtest


# --- Regression ---------------------------------------------------------------

def test_a_regression_backtest_matches_the_arithmetic():
    """Fifty rows, realised 0..49, every prediction exactly 2 too high.

        every error = +2      so  RMSE = 2, MAE = 2, bias = +2
        ss_residual = 50 * 2^2                       = 200
        ss_total    = n(n^2 - 1)/12 = 50*2499/12     = 10412.5
        R^2         = 1 - 200/10412.5                = 0.980792
    """
    realised = [float(i) for i in range(50)]
    predicted = [r + 2 for r in realised]

    outcome = backtest(predicted, realised, FIELD_TYPE_REGRESSION)
    metrics = outcome["detail"]["metrics"]

    assert metrics["rmse"] == 2.0
    assert metrics["mae"] == 2.0
    assert metrics["bias"] == 2.0, "positive: it predicts high, which is correctable"
    ss_total = 50 * (50 ** 2 - 1) / 12
    assert abs(metrics["r2"] - (1 - 200 / ss_total)) < 1e-12
    assert abs(metrics["r2"] - 0.980792) < 1e-6


def test_bias_says_which_way_where_the_error_metrics_only_say_how_far():
    """Two books with identical RMSE and MAE: one consistently high, one scattered.
    A model that is always 2 out is one somebody can correct."""
    realised = [float(i) for i in range(50)]
    always_high = backtest([r + 2 for r in realised], realised, FIELD_TYPE_REGRESSION)
    scattered = backtest([r + (2 if i % 2 else -2) for i, r in enumerate(realised)],
                         realised, FIELD_TYPE_REGRESSION)

    assert always_high["detail"]["metrics"]["rmse"] == scattered["detail"]["metrics"]["rmse"]
    assert always_high["detail"]["metrics"]["bias"] == 2.0
    assert scattered["detail"]["metrics"]["bias"] == 0.0


def test_a_regression_backtest_reports_the_regression_metrics_and_no_others():
    """No AUC on a continuous field. The metric list is config, and this is what stops
    a classifier's vocabulary leaking onto half the estate."""
    realised = [float(i) for i in range(50)]
    outcome = backtest([r + 1 for r in realised], realised, FIELD_TYPE_REGRESSION)
    assert set(outcome["detail"]["metrics"]) == set(BACKTEST_METRICS[FIELD_TYPE_REGRESSION])
    assert outcome["detail"]["headline"] == "r2"


def test_identical_realised_values_leave_r_squared_undefined():
    """R² divides by the variance of what actually happened. Where there was none,
    "explains no variance" is not a fair reading — there was nothing to explain."""
    outcome = backtest([1.0] * 60, [5.0] * 60, FIELD_TYPE_REGRESSION)
    assert outcome["status"] == STATUS_UNDEFINED
    assert outcome["value"] is None and outcome["rag"] is None
    assert "identical" in outcome["detail"]


# --- Classification -----------------------------------------------------------

def test_a_classification_backtest_matches_the_arithmetic():
    """Fifty rows. 25 A, all predicted A. 25 B, of which 20 predicted B and 5 A.

        accuracy   = 45/50                                  = 0.9
        A: precision 25/30 = 0.833333, recall 25/25 = 1.0
        B: precision 20/20 = 1.0,      recall 20/25 = 0.8
        macro precision = (0.833333 + 1.0) / 2              = 0.916667
        macro recall    = (1.0 + 0.8) / 2                   = 0.9
        F1(A) = 2*0.833333*1.0/1.833333                     = 0.909091
        F1(B) = 2*1.0*0.8/1.8                               = 0.888889
        macro F1                                            = 0.898990
    """
    realised = ["A"] * 25 + ["B"] * 25
    predicted = ["A"] * 25 + ["B"] * 20 + ["A"] * 5

    metrics = backtest(predicted, realised, FIELD_TYPE_CLASSIFICATION)["detail"]["metrics"]
    assert metrics["accuracy"] == 45 / 50
    assert abs(metrics["precision"] - (25 / 30 + 1.0) / 2) < 1e-12
    assert abs(metrics["recall"] - (1.0 + 0.8) / 2) < 1e-12
    f1_a = 2 * (25 / 30) * 1.0 / ((25 / 30) + 1.0)
    f1_b = 2 * 1.0 * 0.8 / (1.0 + 0.8)
    assert abs(metrics["f1"] - (f1_a + f1_b) / 2) < 1e-12
    assert abs(metrics["f1"] - 0.898990) < 1e-6


def test_classes_are_averaged_evenly_so_a_rare_class_still_counts():
    """Macro, not weighted. 90 of one class predicted perfectly and 10 of another
    missed entirely is not a 90% model to a model risk function — a weighted average is
    designed to let the majority class answer for the minority."""
    realised = ["A"] * 90 + ["B"] * 10
    predicted = ["A"] * 100

    metrics = backtest(predicted, realised, FIELD_TYPE_CLASSIFICATION)["detail"]["metrics"]
    assert metrics["accuracy"] == 0.9
    # B is never predicted: its recall is 0, and macro F1 halves accordingly.
    assert metrics["recall"] == (1.0 + 0.0) / 2
    assert metrics["f1"] < 0.5, "the headline must not read as a 90% model"


def test_a_perfect_classifier_scores_one():
    realised = ["A"] * 30 + ["B"] * 30
    metrics = backtest(realised, realised, FIELD_TYPE_CLASSIFICATION)["detail"]["metrics"]
    assert metrics == {"accuracy": 1.0, "precision": 1.0, "recall": 1.0, "f1": 1.0}


# --- Degenerate input ---------------------------------------------------------

def test_backtest_declines_on_too_few_pairs_and_on_none():
    assert backtest([], [], FIELD_TYPE_REGRESSION)["status"] == STATUS_NO_DATA
    few = backtest([1.0] * 5, [1.0] * 5, FIELD_TYPE_REGRESSION)
    assert few["status"] == STATUS_INSUFFICIENT_SAMPLE
    assert str(MIN_SAMPLE[BACKTEST]) in few["detail"]


def test_an_unpaired_observation_is_dropped_rather_than_shifted():
    """Element i of each side is the same subject."""
    realised = [float(i) for i in range(60)]
    predicted = [None if i == 0 else float(i) for i in range(60)]
    assert backtest(predicted, realised, FIELD_TYPE_REGRESSION)["n"] == 59


def test_non_numeric_values_on_a_regression_field_are_undefined_not_zero():
    outcome = backtest(["n/a"] * 60, ["n/a"] * 60, FIELD_TYPE_REGRESSION)
    assert outcome["status"] == STATUS_UNDEFINED


def test_an_unknown_field_type_is_a_programming_error_not_a_finding():
    """The one case that DOES raise: a caller asking for a field type nothing defines
    has a bug, and returning a status would bury it in a monitoring report."""
    with pytest.raises(ValueError, match="unknown field type"):
        backtest([1.0] * 60, [1.0] * 60, "astrology")


def test_the_headline_carries_the_rating_and_the_rest_travel_with_it():
    """A report needs one colour and a committee will ask what the others were."""
    realised = [float(i) for i in range(60)]
    outcome = backtest([r + 0.5 for r in realised], realised, FIELD_TYPE_REGRESSION)
    assert outcome["status"] == STATUS_OK
    assert outcome["rag"] == "Green"
    assert outcome["value"] == outcome["detail"]["metrics"]["r2"]
    assert math.isfinite(outcome["value"])
