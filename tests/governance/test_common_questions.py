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
"""The common questionnaire: authored once, composed onto every application of a model.

The two lists had "Use Case" and "Explainability" worded differently — "what decision
does this model inform" against "what decision or task does this system support" —
which reads as a distinction and is not one. Two populations answering differently
worded versions of one question cannot be reported together.

Three of the five were on one list and not the other, which was the real finding: only
AI Systems were asked who could be disadvantaged, though a model that ranks retail
applicants raises that exactly as a generative system does.
"""
from __future__ import annotations

from config.governance import REFERENCE_LISTS, REFERENCE_SPECS
from config.governance._ai import AI_SYSTEM_QUESTIONS
from config.governance._ml import ML_APPLICATION_QUESTIONS
from config.governance._questions_common import (COMMON_QUESTION_LIST,
                                                 COMMON_QUESTIONS)
from src.governance.ai_system import get_ai_system, register_ai_system
from src.governance.ai_system.projection import rebuild_ai_system_view
from src.governance.ml_application import (get_ml_application, register_ml_application)
from src.governance.ml_application.projection import rebuild_ml_application_view
from src.governance.reference import (ensure_default_common_questions,
                                      ensure_default_estimators,
                                      get_reference_lists, update_option)
from src.governance.seeding import compose_questions

_LABELS = lambda qs: [q["short_label"] for q in qs]  # noqa: E731


def _register_ml(ml_application_id):
    """An ML Application needs an estimator the institution has registered."""
    ensure_default_estimators()
    register_ml_application(ml_application_id=ml_application_id, fields={
        "name": "Retail PD scorecard", "division": "Risk", "owner": "A",
        "use_case": "Ranks applications.", "estimator": "LogisticRegression"},
        actor="admin")
    rebuild_ml_application_view()


# --- 1.1 the list ------------------------------------------------------------

def test_common_list_seeds_on_a_fresh_database():
    assert ensure_default_common_questions() == len(COMMON_QUESTIONS)
    seeded = get_reference_lists()[COMMON_QUESTION_LIST]
    assert _LABELS(seeded) == _LABELS(COMMON_QUESTIONS)
    # Seeds a vacuum, never reconciles a curated one.
    assert ensure_default_common_questions() == 0


def test_common_questions_match_the_shared_shape():
    """Same keys as the ML and AI lists, so one composition helper handles all three
    and nothing downstream can tell which list a question came from."""
    keys = {frozenset(q) for q in COMMON_QUESTIONS}
    assert keys == {frozenset(q) for q in ML_APPLICATION_QUESTIONS}
    assert keys == {frozenset(q) for q in AI_SYSTEM_QUESTIONS}
    assert keys == {frozenset({"short_label", "question"})}


def test_the_list_is_registered_like_every_other_reference_list():
    assert COMMON_QUESTION_LIST in REFERENCE_LISTS
    spec = REFERENCE_SPECS[COMMON_QUESTION_LIST]
    assert spec["id_prefix"] == "CQ" and spec["display"] == "short_label"


# --- 1.3 disjointness ---------------------------------------------------------

def test_the_three_lists_are_disjoint_on_short_label():
    """No question text lives in two lists. This is the test the whole split exists
    for: a duplicated topic means one question asked twice, in two wordings, and
    answered inconsistently."""
    common, ml, ai = (set(_LABELS(qs)) for qs in
                      (COMMON_QUESTIONS, ML_APPLICATION_QUESTIONS, AI_SYSTEM_QUESTIONS))
    assert not common & ml, f"common and ML share {common & ml}"
    assert not common & ai, f"common and AI share {common & ai}"
    assert not ml & ai, f"ML and AI share {ml & ai}"


def test_what_is_left_on_each_list_is_particular_to_it():
    """The processes stay separate — only the genuinely shared questions moved."""
    assert "Training Data" in _LABELS(ML_APPLICATION_QUESTIONS)
    assert "Data Leakage" in _LABELS(ML_APPLICATION_QUESTIONS)
    assert "Agency and Authority" in _LABELS(AI_SYSTEM_QUESTIONS)
    assert "Hallucination Exposure" in _LABELS(AI_SYSTEM_QUESTIONS)


# --- 1.2 composition ----------------------------------------------------------

def test_composition_puts_the_common_questions_first():
    """Order is part of the contract: a reviewer opening any record meets the same five
    questions in the same order, and a report comparing two record types compares row 1
    with row 1."""
    composed = compose_questions("ml_application_questions", ML_APPLICATION_QUESTIONS)
    assert _LABELS(composed) == _LABELS(COMMON_QUESTIONS) + _LABELS(ML_APPLICATION_QUESTIONS)


def test_registered_ml_app_carries_common_then_ml_questions():
    _register_ml("MLA-1")
    asked = get_ml_application("MLA-1")["data"]["ml_review_questions"]
    assert _LABELS(asked) == _LABELS(COMMON_QUESTIONS) + _LABELS(ML_APPLICATION_QUESTIONS)
    # One flat collection, numbered from one: nothing downstream learns it came from
    # two sources.
    assert asked[0]["item_id"] == "MLQ-001"


def test_registered_ai_system_carries_common_then_ai_questions():
    register_ai_system(ai_system_id="AIS-1", fields={
        "name": "Summariser", "division": "Risk", "owner": "A",
        "use_case": "Summarises correspondence.",
        "deployment_pattern": "Direct prompting"}, actor="admin")
    rebuild_ai_system_view()
    asked = get_ai_system("AIS-1")["data"]["ai_review_questions"]
    assert _LABELS(asked) == _LABELS(COMMON_QUESTIONS) + _LABELS(AI_SYSTEM_QUESTIONS)


def test_both_record_types_are_asked_the_same_five_first():
    """The point of the shared list, stated as a test: whatever the record is, the
    first five questions put to it are the same five."""
    _register_ml("MLA-2")
    register_ai_system(ai_system_id="AIS-2", fields={
        "name": "B", "division": "Risk", "owner": "A", "use_case": "y",
        "deployment_pattern": "Direct prompting"}, actor="admin")
    rebuild_ml_application_view()
    rebuild_ai_system_view()
    n = len(COMMON_QUESTIONS)
    ml = get_ml_application("MLA-2")["data"]["ml_review_questions"][:n]
    ai = get_ai_system("AIS-2")["data"]["ai_review_questions"][:n]
    assert [q["question"] for q in ml] == [q["question"] for q in ai]


def test_editing_a_common_question_does_not_rewrite_an_existing_record():
    """A record keeps the questionnaire it was registered with. A review answers the
    question that was actually put to it, so rewording the list afterwards must not
    change what an answered record was asked."""
    ensure_default_common_questions()
    _register_ml("MLA-3")
    before = get_ml_application("MLA-3")["data"]["ml_review_questions"][0]["question"]

    first = get_reference_lists()[COMMON_QUESTION_LIST][0]
    update_option(list_name=COMMON_QUESTION_LIST, item_id=first["item_id"],
                  fields={"question": "Reworded entirely."}, actor="admin")

    rebuild_ml_application_view()
    after = get_ml_application("MLA-3")["data"]["ml_review_questions"][0]["question"]
    assert after == before


def test_a_record_registered_after_an_edit_is_asked_the_new_wording():
    """The other half of the same rule: the institution's edit reaches everything
    registered from then on."""
    ensure_default_common_questions()
    first = get_reference_lists()[COMMON_QUESTION_LIST][0]
    update_option(list_name=COMMON_QUESTION_LIST, item_id=first["item_id"],
                  fields={"question": "Our own wording."}, actor="admin")

    _register_ml("MLA-4")
    asked = get_ml_application("MLA-4")["data"]["ml_review_questions"]
    assert asked[0]["question"] == "Our own wording."


def test_composition_falls_back_to_the_shipped_set_on_an_unseeded_database():
    """A fresh database before the first-run seed still composes a full questionnaire —
    the fallback the AI list has always relied on, now shared by all three."""
    assert not get_reference_lists().get(COMMON_QUESTION_LIST), "nothing seeded yet"
    composed = compose_questions("ml_application_questions", ML_APPLICATION_QUESTIONS)
    assert _LABELS(composed) == _LABELS(COMMON_QUESTIONS) + _LABELS(ML_APPLICATION_QUESTIONS)
