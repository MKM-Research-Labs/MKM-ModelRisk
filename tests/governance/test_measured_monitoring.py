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
"""The measured monitoring position: what the statistics say, or why they cannot.

The rule the whole thing turns on is that an absent measurement and a measurement of no
change are different claims. A monitoring pack that reports a zero where it should
report "nobody recorded a baseline" is worse than one that reports nothing, because a
committee acts on the zero.
"""
from __future__ import annotations

from config.governance._assessments import MONITORING_COLLECTION
from config.governance._monitoring_measures import (BACKTEST, PSI, STATUS_NO_DATA,
                                                    STATUS_OK)
from src.governance.monitoring.measured import measure_observation, measured_position
from src.governance.monitoring.report import build_monitoring_tex

_SETTINGS = {"fields": {"org_name": "MKM"}}


def _record(*observations):
    return {"name": "Retail PD scorecard", MONITORING_COLLECTION: list(observations)}


def _by_measure(results, measure):
    return next(r for r in results if r["measure"] == measure)


# --- Nothing recorded ---------------------------------------------------------

def test_ml_app_without_outcomes_reads_not_evidenced():
    position = measured_position(_record())
    assert position["evidenced"] is False
    assert position["results"] == []
    assert "absence of a measurement, not a measurement of no change" in position["why"]


def test_a_record_with_nothing_recorded_reads_as_one_absence_not_four_failures():
    """Four unmeasurable measures would look like four problems. There is one: nobody
    has recorded the data."""
    assert measured_position({})["results"] == []


def test_the_report_states_the_absence_rather_than_omitting_the_section():
    tex = build_monitoring_tex({"model_id": "M-1", "data": _record()}, _SETTINGS,
                               "2026-09-05", found=[], configured=False)
    assert "No monitoring observation has been recorded" in tex


# --- Recorded and measurable --------------------------------------------------

def test_ml_app_with_outcomes_reports_psi_and_backtest():
    """Enough rows for both: 200 predictions against realised, and a distribution that
    has moved."""
    predicted = ",".join(["1"] * 100 + ["2"] * 100)
    realised = ",".join(["1"] * 90 + ["2"] * 110)
    results = measured_position(_record({
        "field": "severity band", "field_type": "classification",
        "buckets": "1,2", "baseline_counts": "600,400", "current_counts": "300,700",
        "predicted": predicted, "realised": realised,
    }))
    assert results["evidenced"] is True

    stability = _by_measure(results["results"], PSI)
    assert stability["status"] == STATUS_OK
    assert stability["rag"] == "Red", "a 60/40 book that is now 30/70 has moved"
    assert stability["field"] == "severity band"

    scored = _by_measure(results["results"], BACKTEST)
    assert scored["status"] == STATUS_OK
    assert scored["value"] is not None


def test_bucket_counts_are_expanded_so_one_index_implementation_serves_both():
    """A monitoring pack carries counts; the library takes observations. Expanding here
    keeps the arithmetic a reviewer checks by hand as the arithmetic that runs."""
    identical = measure_observation({
        "field": "band", "buckets": "a,b", "baseline_counts": "500,500",
        "current_counts": "500,500"})
    assert _by_measure(identical, PSI)["value"] == 0.0


def test_a_regression_field_is_scored_as_one():
    """Half the estate is regression. The field type travels with the observation."""
    values = ",".join(str(float(i)) for i in range(60))
    predicted = ",".join(str(float(i) + 1) for i in range(60))
    results = measure_observation({"field": "expected loss", "field_type": "regression",
                                   "predicted": predicted, "realised": values})
    scored = _by_measure(results, BACKTEST)
    assert scored["status"] == STATUS_OK
    assert set(scored["detail"]["metrics"]) == {"rmse", "mae", "r2", "bias"}


# --- Recorded but not measurable ----------------------------------------------

def test_a_distribution_without_a_baseline_says_which_half_is_missing():
    results = measure_observation({"field": "band", "current_counts": "10,20"})
    stability = _by_measure(results, PSI)
    assert stability["status"] == STATUS_NO_DATA
    assert stability["detail"] == "no baseline distribution recorded"


def test_mismatched_bucket_counts_are_refused_rather_than_zipped():
    """Three baseline buckets against two current ones is not a distribution that
    shifted — it is two different rulers, and zipping them would invent a shift."""
    results = measure_observation({"field": "band", "baseline_counts": "1,2,3",
                                   "current_counts": "1,2"})
    assert "different bucket counts" in _by_measure(results, PSI)["detail"]


def test_an_observation_with_only_a_distribution_says_why_there_is_no_backtest():
    results = measure_observation({"field": "band", "buckets": "a,b",
                                   "baseline_counts": "500,500",
                                   "current_counts": "400,600"})
    scored = _by_measure(results, BACKTEST)
    assert scored["status"] == STATUS_NO_DATA
    assert "no predicted and realised values recorded" in scored["detail"]


def test_transcription_noise_is_tolerated_not_coerced():
    """Somebody types these off a monitoring pack: trailing commas, spaces, a dash for
    a bucket nobody filled."""
    results = measure_observation({"field": "band", "buckets": "a, b",
                                   "baseline_counts": " 500 , 500 , ",
                                   "current_counts": "500,-,500"})
    # The dash is dropped, leaving two current buckets against two baseline ones.
    assert _by_measure(results, PSI)["status"] == STATUS_OK


def test_the_report_prints_the_reason_a_measure_could_not_be_computed():
    tex = build_monitoring_tex(
        {"model_id": "M-2", "data": _record({"field": "band", "buckets": "a,b",
                                             "baseline_counts": "500,500",
                                             "current_counts": "400,600"})},
        _SETTINGS, "2026-09-05", found=[], configured=False)
    assert "Measured monitoring position" in tex
    assert "no predicted and realised values recorded" in tex
