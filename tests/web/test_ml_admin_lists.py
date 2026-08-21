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
"""The two ML admin lists: the Estimator menu and the ML Application questionnaire.

Both are the institution's, not the platform's. The Estimator menu names the
off-the-shelf engines an ML Application can be built on; the questionnaire is what
an ML Application review works through. Neither is shared with the model side --
an ML Application is asked different questions, and the two sets have to be able
to move apart.
"""
from __future__ import annotations

from config.governance import (DEFAULT_ESTIMATORS, ESTIMATOR_LIST,
                               ML_APPLICATION_QUESTIONS, ML_APPLICATION_QUESTION_LIST,
                               REFERENCE_SPECS, REVIEW_QUESTION_LIST, SR262_QUESTIONS)
from src.governance.reference import (ensure_default_estimators,
                                      ensure_default_ml_application_questions,
                                      ensure_default_review_questions,
                                      get_reference_lists)
from tests.web.conftest import HEADERS


def _add(client, list_name, fields):
    return client.post(f"/api/reference/collections/{list_name}",
                       json={"fields": fields, "confirmed": True}, headers=HEADERS)


def test_the_estimator_menu_seeds_a_vacuum_only():
    """An adopter who has trimmed the menu to the libraries it actually runs must not
    find ours back at the next restart."""
    assert ensure_default_estimators() == len(DEFAULT_ESTIMATORS)
    assert len(get_reference_lists()[ESTIMATOR_LIST]) == len(DEFAULT_ESTIMATORS)
    assert ensure_default_estimators() == 0


def test_the_ml_questionnaire_seeds_a_vacuum_only():
    assert ensure_default_ml_application_questions() == len(ML_APPLICATION_QUESTIONS)
    assert len(get_reference_lists()[ML_APPLICATION_QUESTION_LIST]) == len(ML_APPLICATION_QUESTIONS)
    assert ensure_default_ml_application_questions() == 0


def test_seeded_estimators_name_their_source_and_carry_no_versions():
    """The estimator names are universal and we can state them. Which releases an
    institution runs is a fact about their environment, so seeding a guess would put
    releases in their register that nothing in their estate uses."""
    ensure_default_estimators()
    rows = get_reference_lists()[ESTIMATOR_LIST]
    assert {r["source"] for r in rows} == {"scikit-learn", "XGBoost", "LightGBM", "statsmodels"}
    assert all(not r.get("versions") for r in rows)
    by_name = {r["value"]: r for r in rows}
    assert by_name["GradientBoostingRegressor"]["source"] == "scikit-learn"
    assert by_name["XGBRegressor"]["source"] == "XGBoost"


def test_a_new_source_needs_no_release(client):
    """``source`` is a field, not an assumption. An adopter running something we never
    shipped adds it in Admin -- if this needed a code change the field would be filled
    in wrongly instead."""
    ensure_default_estimators()
    assert _add(client, ESTIMATOR_LIST,
                {"value": "CatBoostRegressor", "source": "CatBoost",
                 "versions": "1.2, 1.3"}).status_code == 201
    rows = {r["value"]: r for r in get_reference_lists()[ESTIMATOR_LIST]}
    assert rows["CatBoostRegressor"]["source"] == "CatBoost"
    assert rows["CatBoostRegressor"]["versions"] == "1.2, 1.3"


def test_the_two_questionnaires_move_independently(client):
    """The whole reason for a second list. Editing the ML set must not touch what a
    model review asks, or the separation is cosmetic."""
    ensure_default_review_questions()
    ensure_default_ml_application_questions()
    _add(client, ML_APPLICATION_QUESTION_LIST,
         {"short_label": "Fairness", "question": "Which protected groups were tested for?"})

    lists = get_reference_lists()
    assert len(lists[ML_APPLICATION_QUESTION_LIST]) == len(ML_APPLICATION_QUESTIONS) + 1
    assert len(lists[REVIEW_QUESTION_LIST]) == len(SR262_QUESTIONS)
    assert "Fairness" not in {q["short_label"] for q in lists[REVIEW_QUESTION_LIST]}


def test_both_lists_reach_the_admin_screen(client):
    """A list the Admin API does not expose cannot be maintained, which is how the
    estate ended up with no model types at all."""
    res = client.get("/api/reference").get_json()
    keys = {c["key"]: c for c in res["collections"]}
    assert keys[ESTIMATOR_LIST]["label"] == "Estimator"
    assert keys[ML_APPLICATION_QUESTION_LIST]["label"] == "ML Application questions"
    fields = {f["key"] for f in REFERENCE_SPECS[ESTIMATOR_LIST]["fields"]}
    assert fields == {"value", "source", "versions", "notes"}
