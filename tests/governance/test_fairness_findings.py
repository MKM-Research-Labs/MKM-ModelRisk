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
"""The fairness register as a control: a measured disparity that nobody has answered.

The register held findings and no conclusions, so nothing downstream could act on it
and nothing did. What makes it a control is not the verdict field on its own — it is
that an unanswered adverse verdict stops a review being signed off, and that the only
way to answer one is to assess the attribute again and say what changed.
"""
from __future__ import annotations

from config.governance._assessments import (ADVERSE_FAIRNESS_VERDICT,
                                            VALID_FAIRNESS_VERDICTS)
from src.governance.assessments import (current_fairness_position,
                                        open_failed_evaluations,
                                        open_fairness_findings)


def _data(*rows):
    return {"fairness_assessments": [
        {"item_id": f"FAIR-{i + 1:03d}", **row} for i, row in enumerate(rows)]}


# --- What the register currently says ----------------------------------------

def test_the_latest_row_for_an_attribute_is_the_firms_position():
    data = _data({"attribute": "Age band", "verdict": "Disparity found"},
                 {"attribute": "Age band", "verdict": "Within tolerance"})
    assert [r["item_id"] for r in current_fairness_position(data)] == ["FAIR-002"]
    assert open_fairness_findings(data) == []


def test_the_same_attribute_spelt_differently_is_the_same_attribute():
    """``attribute`` is free text on purpose — which characteristics are protected is a
    matter of law and differs by jurisdiction — so the reading has to be forgiving."""
    data = _data({"attribute": "Age band", "verdict": ADVERSE_FAIRNESS_VERDICT},
                 {"attribute": "  age   BAND ", "verdict": "No disparity found"})
    assert open_fairness_findings(data) == []


def test_assessing_a_different_attribute_does_not_answer_a_finding():
    """The obvious way to game a gate like this: measure something easier and move on."""
    data = _data({"attribute": "Age band", "verdict": ADVERSE_FAIRNESS_VERDICT},
                 {"attribute": "Postcode", "verdict": "No disparity found"})
    assert [r["attribute"] for r in open_fairness_findings(data)] == ["Age band"]


def test_an_unanswered_disparity_stays_open():
    data = _data({"attribute": "Age band", "verdict": ADVERSE_FAIRNESS_VERDICT})
    assert len(open_fairness_findings(data)) == 1


def test_a_later_disparity_reopens_an_attribute_that_was_clear():
    data = _data({"attribute": "Age band", "verdict": "No disparity found"},
                 {"attribute": "Age band", "verdict": ADVERSE_FAIRNESS_VERDICT})
    assert [r["item_id"] for r in open_fairness_findings(data)] == ["FAIR-002"]


# --- What does NOT block -----------------------------------------------------

def test_a_row_recorded_before_verdicts_existed_does_not_block():
    """The estate is full of rows with no verdict. Adding this must not retrospectively
    stop every review in the firm — a blank verdict means no verdict was reached, which
    is not a finding of disparity."""
    assert open_fairness_findings(_data({"attribute": "Age band"})) == []
    assert open_fairness_findings(_data({"attribute": "Age", "verdict": ""})) == []


def test_inconclusive_does_not_block():
    """It says nobody knows yet. Blocking on it would train people out of the word."""
    assert open_fairness_findings(_data({"attribute": "Age", "verdict": "Inconclusive"})) == []


def test_a_record_with_no_assessments_has_no_findings():
    assert open_fairness_findings({}) == []
    assert current_fairness_position({}) == []


def test_the_adverse_verdict_is_one_of_the_offered_ones():
    """A gate keyed to a value the form cannot produce is a gate that never fires."""
    assert ADVERSE_FAIRNESS_VERDICT in VALID_FAIRNESS_VERDICTS


# --- Evaluations, on the same reasoning --------------------------------------

def _evals(*rows):
    return {"evaluations": [
        {"item_id": f"EVAL-{i + 1:03d}", **row} for i, row in enumerate(rows)]}


def test_a_failed_evaluation_stands_until_that_kind_is_run_again():
    data = _evals({"kind": "Adversarial / red team", "passed": "Failed"})
    assert [r["item_id"] for r in open_failed_evaluations(data)] == ["EVAL-001"]

    rerun = _evals({"kind": "Adversarial / red team", "passed": "Failed"},
                   {"kind": "Adversarial / red team", "passed": "Passed"})
    assert open_failed_evaluations(rerun) == []


def test_passing_a_different_kind_does_not_answer_a_failure():
    """Keyed by kind, because the question is "does it pass its red team", not "did run
    14 pass". A held-out score does not answer a red-team failure."""
    data = _evals({"kind": "Adversarial / red team", "passed": "Failed"},
                  {"kind": "Held-out performance", "passed": "Passed"})
    assert [r["kind"] for r in open_failed_evaluations(data)] == ["Adversarial / red team"]


def test_passed_with_caveats_does_not_block():
    """The caveats are what the record of challenge is for."""
    data = _evals({"kind": "Held-out performance", "passed": "Passed with caveats"})
    assert open_failed_evaluations(data) == []


def test_an_evaluation_with_no_verdict_does_not_block():
    """An exploratory red-team run has findings and no pass mark — that is why the
    verdict is allowed to be blank, and it must not be read as a failure."""
    assert open_failed_evaluations(_evals({"kind": "Adversarial / red team"})) == []
