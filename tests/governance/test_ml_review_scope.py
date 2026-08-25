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
"""One record's review, scoped to the policy its division ratified."""
from __future__ import annotations

from config.governance import (ML_REVIEW_QUESTIONS_COLLECTION, QUESTION_ITEM_SOURCE,
                               TRAINING_ITEM_SOURCE, TRAINING_RUNS_COLLECTION,
                               policy_item_id)
from src.governance.ml_application.review_scope import is_complete, review_scope
from src.governance.ml_review_policy import (approve_ml_review_policy,
                                             propose_ml_review_policy)

DIV = "PhysicalRisk"
TASK = policy_item_id(TRAINING_ITEM_SOURCE, "learning_task")
TARGET = policy_item_id(TRAINING_ITEM_SOURCE, "target_definition")


def _ratify(policy, division=DIV):
    propose_ml_review_policy(division=division, policy=policy, actor="admin")
    approve_ml_review_policy(division=division, actor="chair")


def _record(train=None, questions=None, division=DIV):
    return {"division": division,
            TRAINING_RUNS_COLLECTION: [train] if train else [],
            ML_REVIEW_QUESTIONS_COLLECTION: questions or []}


def test_an_unratified_estate_asks_for_everything_and_requires_nothing():
    scope = review_scope(_record({"fit_id": "1.0", "learning_task": "Binary classification"}))
    assert scope["training"]["total"] > 40
    assert scope["training"]["mandatory_total"] == 0
    assert scope["missing_mandatory"] == []
    assert is_complete(_record()) is True


def test_switching_fields_off_shrinks_what_progress_is_measured_against():
    train = {"fit_id": "1.0", "learning_task": "Binary classification"}
    before = review_scope(_record(train))["training"]["total"]
    _ratify({TARGET: {"in_use": False, "mandatory": False}})
    after = review_scope(_record(train))["training"]["total"]
    assert after == before - 1


def test_a_mandatory_field_left_blank_is_named_not_counted():
    _ratify({TASK: {"in_use": True, "mandatory": True}})
    scope = review_scope(_record({"fit_id": "1.0"}))
    assert scope["training"]["missing_mandatory"] == ["Learning task"]
    assert is_complete(_record({"fit_id": "1.0"})) is False
    # Filled, and it stops being outstanding.
    filled = _record({"fit_id": "1.0", "learning_task": "Binary classification"})
    assert review_scope(filled)["training"]["missing_mandatory"] == []
    assert is_complete(filled) is True


def test_a_mandatory_field_that_does_not_apply_is_not_withheld():
    """A classifier is not blocked for want of a field only a regression is asked."""
    target_dist = policy_item_id(TRAINING_ITEM_SOURCE, "target_distribution")
    _ratify({target_dist: {"in_use": True, "mandatory": True}})
    # ``target_distribution`` is conditional on a classification task.
    regression = _record({"fit_id": "1.0", "learning_task": "Regression"})
    assert review_scope(regression)["training"]["missing_mandatory"] == []
    assert is_complete(regression) is True


def test_progress_and_permission_are_separate_figures():
    """A record can be far from complete and still be completable."""
    _ratify({TASK: {"in_use": True, "mandatory": True}})
    scope = review_scope(_record({"fit_id": "1.0", "learning_task": "Regression"}))
    assert scope["training"]["filled"] < scope["training"]["total"]   # plenty missing
    assert scope["missing_mandatory"] == []                          # yet completable


# --- Questions --------------------------------------------------------------

def _q(label, status=""):
    return {"item_id": "VQ-001", "short_label": label, "status": status}


def test_questions_the_policy_never_mentions_are_still_asked():
    """A record migrated from a model carries the MODEL's questions, which are not in
    the ML register. They must not drop off its own review."""
    scope = review_scope(_record(questions=[_q("Ronseal Test"), _q("Override Controls")]))
    assert scope["questions"]["total"] == 2
    assert scope["question_in_use"] == ["Ronseal Test", "Override Controls"]


def test_a_question_can_be_switched_off_and_made_mandatory():
    off = policy_item_id(QUESTION_ITEM_SOURCE, "Override Controls")
    req = policy_item_id(QUESTION_ITEM_SOURCE, "Ronseal Test")
    _ratify({off: {"in_use": False, "mandatory": False},
             req: {"in_use": True, "mandatory": True}})
    rec = _record(questions=[_q("Ronseal Test"), _q("Override Controls")])
    scope = review_scope(rec)
    assert scope["questions"]["total"] == 1              # the switched-off one is hidden
    assert scope["questions"]["missing_mandatory"] == ["Ronseal Test"]
    assert is_complete(rec) is False


def test_an_addressed_question_satisfies_the_requirement():
    req = policy_item_id(QUESTION_ITEM_SOURCE, "Ronseal Test")
    _ratify({req: {"in_use": True, "mandatory": True}})
    rec = _record(questions=[_q("Ronseal Test", "Addressed")])
    assert review_scope(rec)["questions"]["answered"] == 1
    assert is_complete(rec) is True


def test_not_addressed_is_not_an_answer():
    req = policy_item_id(QUESTION_ITEM_SOURCE, "Ronseal Test")
    _ratify({req: {"in_use": True, "mandatory": True}})
    rec = _record(questions=[_q("Ronseal Test", "Not Addressed")])
    assert review_scope(rec)["questions"]["answered"] == 0
    assert is_complete(rec) is False


def test_both_halves_report_into_one_outstanding_list():
    _ratify({TASK: {"in_use": True, "mandatory": True},
             policy_item_id(QUESTION_ITEM_SOURCE, "Ronseal Test"):
                 {"in_use": True, "mandatory": True}})
    rec = _record({"fit_id": "1.0"}, [_q("Ronseal Test")])
    assert review_scope(rec)["missing_mandatory"] == ["Learning task", "Ronseal Test"]


def test_a_division_that_ratified_nothing_is_unaffected_by_anothers_policy():
    _ratify({TASK: {"in_use": False, "mandatory": False}})
    other = review_scope(_record({"fit_id": "1.0"}, division="Ratings"))
    assert "learning_task" in other["training_in_use"]


def test_a_mandatory_question_off_the_register_is_marked_as_well_as_enforced():
    """The screen's red rule and the gate must agree.

    Deriving the marked list from the register's catalogue enforced a requirement the
    page never marked: refused at the gate, with nothing on the record to say why. A
    record migrated from a model carries questions no ML register lists, so this is
    the ordinary case, not an edge one.
    """
    req = policy_item_id(QUESTION_ITEM_SOURCE, "Ronseal Test")   # not in the register
    _ratify({req: {"in_use": True, "mandatory": True}})
    rec = _record(questions=[_q("Ronseal Test"), _q("Override Controls")])
    scope = review_scope(rec)
    assert scope["question_mandatory"] == ["Ronseal Test"]        # marked
    assert scope["questions"]["missing_mandatory"] == ["Ronseal Test"]   # and enforced
