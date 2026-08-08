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
"""The review questionnaire belongs to the institution, not to the platform.

The nine SR 26-2 questions are where an adopter starts, not what it is stuck with:
one under a different regulator rewords them, drops what does not apply and adds
its own. So the set is an admin list, and a model is copied it at registration —
which means a model keeps the questions it was actually asked even after the list
moves on, and editing the list never rewrites an answer somebody has given.
"""
from __future__ import annotations

from config.governance import REVIEW_QUESTION_LIST, SR262_QUESTIONS
from src.governance.reference import (ensure_default_review_questions,
                                      get_reference_lists)
from tests.web.conftest import HEADERS


def _questions(client, model_id="M1"):
    return client.get(f"/api/models/{model_id}").get_json()["data"]["validation_questions"]


def _register(client, model_id="M1"):
    return client.post("/api/models",
                       json={"model_id": model_id, "name": "Alpha", "confirmed": True},
                       headers=HEADERS)


def _add_question(client, short_label, question):
    return client.post(f"/api/reference/collections/{REVIEW_QUESTION_LIST}",
                       json={"fields": {"short_label": short_label, "question": question},
                             "confirmed": True}, headers=HEADERS)


def test_the_shipped_set_seeds_a_vacuum_only():
    """Nine to start with; an adopter who has since curated the list must not find
    the defaults back at the next restart."""
    assert ensure_default_review_questions() == len(SR262_QUESTIONS)
    assert len(get_reference_lists()[REVIEW_QUESTION_LIST]) == 9
    assert ensure_default_review_questions() == 0


def test_a_model_is_asked_the_institutions_questions(client):
    _add_question(client, "Ronseal Test", "Does the model do what it says on the tin?")
    _add_question(client, "Client impact", "Who is harmed first if this model is wrong?")
    _register(client)
    asked = _questions(client)
    assert [q["short_label"] for q in asked] == ["Ronseal Test", "Client impact"]
    assert asked[1]["question"] == "Who is harmed first if this model is wrong?"
    assert asked[0]["item_id"] == "VQ-001"


def test_editing_the_list_does_not_rewrite_answers_already_given(client):
    """A model keeps the questions it was actually asked. Anything else would let a
    later edit silently restate what a reviewer signed off against."""
    _add_question(client, "Client impact", "Who is harmed first if this model is wrong?")
    _register(client)
    item_id = _questions(client)[0]["item_id"]
    client.post(f"/api/models/M1/collections/validation_questions/{item_id}",
                json={"fields": {"status": "Addressed", "rationale": "Retail book only."},
                      "confirmed": True}, headers=HEADERS)

    lists = get_reference_lists()[REVIEW_QUESTION_LIST]
    client.post(f"/api/reference/collections/{REVIEW_QUESTION_LIST}/{lists[0]['item_id']}",
                json={"fields": {"question": "Something else entirely"}, "confirmed": True},
                headers=HEADERS)

    kept = _questions(client)[0]
    assert kept["question"] == "Who is harmed first if this model is wrong?"
    assert kept["rationale"] == "Retail book only."
    # ...while the next model registered is asked the new one.
    _register(client, "M2")
    assert _questions(client, "M2")[0]["question"] == "Something else entirely"


def test_an_empty_list_still_registers_a_model_with_the_shipped_set(client):
    """A database that has never been seeded must not produce a model with no
    questions at all — an unasked questionnaire is worse than a default one."""
    assert not get_reference_lists()[REVIEW_QUESTION_LIST]
    _register(client)
    assert len(_questions(client)) == len(SR262_QUESTIONS)
