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
"""The institution decides what its ML review asks for, and its MRC ratifies it.

The catalogue is ours; which of it applies is theirs. These hold the two halves of
that: the default is permissive so an estate running today sees no change, and
tightening it takes a committee.
"""
from __future__ import annotations

import pytest

from config.governance import (ML_APPLICATION_QUESTION_LIST, QUESTION_ITEM_SOURCE,
                               TRAINING_ITEM_SOURCE, policy_item_id)
from src.governance.errors import DomainError
from src.governance.ml_review_policy import (approve_ml_review_policy, catalogue,
                                             get_ml_review_policy,
                                             get_ml_review_policy_draft, in_use_keys,
                                             load, mandatory_keys,
                                             propose_ml_review_policy,
                                             reject_ml_review_policy, resolved_policy)
from src.governance.reference import add_option

DIV = "PhysicalRisk"
LEARNING_TASK = policy_item_id(TRAINING_ITEM_SOURCE, "learning_task")
TARGET = policy_item_id(TRAINING_ITEM_SOURCE, "target_definition")


def _propose(policy, division=DIV):
    return propose_ml_review_policy(division=division, policy=policy, actor="admin")


# --- The default ------------------------------------------------------------

def test_an_estate_that_has_said_nothing_gets_everything_and_requires_nothing():
    """The T6 position: shipping this changes no screen until somebody decides."""
    resolved = resolved_policy(DIV)
    assert resolved, "the catalogue must not be empty"
    assert all(item["in_use"] for item in resolved.values())
    assert not any(item["mandatory"] for item in resolved.values())
    assert mandatory_keys(DIV) == ()


def test_the_catalogue_covers_the_training_fields_and_the_questions():
    add_option(list_name=ML_APPLICATION_QUESTION_LIST,
               fields={"short_label": "Benchmarking",
                       "question": "Has it been benchmarked?"}, actor="admin")
    sources = {item["source"] for item in catalogue()}
    assert sources == {TRAINING_ITEM_SOURCE, QUESTION_ITEM_SOURCE}
    labels = [item["label"] for item in catalogue()
              if item["source"] == QUESTION_ITEM_SOURCE]
    assert "Benchmarking" in labels


# --- Ratification -----------------------------------------------------------

def test_a_draft_changes_nothing_until_the_committee_approves_it():
    _propose({LEARNING_TASK: {"in_use": True, "mandatory": True}})
    assert get_ml_review_policy_draft(DIV) == {
        LEARNING_TASK: {"in_use": True, "mandatory": True}}
    # Still permissive: a proposal is not a policy.
    assert mandatory_keys(DIV) == ()
    assert load(DIV)["state"] == "draft"

    approve_ml_review_policy(division=DIV, actor="chair", meeting_id="MRC-PR-Q1")
    assert mandatory_keys(DIV) == ("learning_task",)
    assert get_ml_review_policy_draft(DIV) is None
    assert load(DIV)["state"] == "approved"


def test_a_rejected_draft_leaves_the_live_policy_alone():
    _propose({LEARNING_TASK: {"in_use": True, "mandatory": True}})
    approve_ml_review_policy(division=DIV, actor="chair")
    _propose({TARGET: {"in_use": False, "mandatory": False}})
    reject_ml_review_policy(division=DIV, actor="chair", reason="too soon")
    assert mandatory_keys(DIV) == ("learning_task",)
    assert "target_definition" in in_use_keys(DIV)


def test_approving_or_rejecting_nothing_is_refused():
    with pytest.raises(DomainError, match="no proposed ML review policy"):
        approve_ml_review_policy(division=DIV, actor="chair")
    with pytest.raises(DomainError, match="no proposed ML review policy"):
        reject_ml_review_policy(division=DIV, actor="chair")


def test_one_divisions_policy_does_not_reach_another():
    _propose({LEARNING_TASK: {"in_use": False, "mandatory": False}})
    approve_ml_review_policy(division=DIV, actor="chair")
    assert "learning_task" not in in_use_keys(DIV)
    assert "learning_task" in in_use_keys("Ratings")


def test_a_policy_must_belong_to_a_division():
    with pytest.raises(DomainError, match="must belong to a division"):
        _propose({}, division="  ")


# --- What a policy may say --------------------------------------------------

def test_mandatory_while_not_in_use_is_refused():
    """A committee should never ratify "required, and shown to nobody"."""
    with pytest.raises(DomainError, match="cannot be mandatory while it is not in use"):
        _propose({LEARNING_TASK: {"in_use": False, "mandatory": True}})


@pytest.mark.parametrize("policy, match", [
    ([], "must be an object"),
    ({"nonsense": {"in_use": True}}, "not a reviewable item id"),
    ({"training:": {"in_use": True}}, "not a reviewable item id"),
    ({LEARNING_TASK: "yes"}, "must be an object"),
    ({LEARNING_TASK: {"in_use": "yes"}}, "must be true or false"),
])
def test_a_malformed_policy_never_reaches_the_committee(policy, match):
    with pytest.raises(DomainError, match=match):
        _propose(policy)


def test_an_item_that_has_since_been_deleted_does_not_invalidate_the_policy():
    """A question removed in Admin must not force the committee to re-ratify."""
    stale = policy_item_id(QUESTION_ITEM_SOURCE, "MLQ-gone")
    _propose({stale: {"in_use": True, "mandatory": True}})
    approve_ml_review_policy(division=DIV, actor="chair")
    # It resolves against a catalogue that no longer lists it: it does nothing.
    assert stale not in resolved_policy(DIV)
    assert mandatory_keys(DIV, source=QUESTION_ITEM_SOURCE) == ()


def test_switching_an_item_off_hides_it_without_touching_what_was_recorded():
    """Decision 3: un-ticking is not a deletion, and re-ticking brings it back."""
    _propose({TARGET: {"in_use": False, "mandatory": False}})
    approve_ml_review_policy(division=DIV, actor="chair")
    assert "target_definition" not in in_use_keys(DIV)
    _propose({})
    approve_ml_review_policy(division=DIV, actor="chair")
    assert "target_definition" in in_use_keys(DIV)


def test_the_live_policy_is_what_was_approved_not_what_was_last_proposed():
    _propose({LEARNING_TASK: {"in_use": True, "mandatory": True}})
    approve_ml_review_policy(division=DIV, actor="chair")
    _propose({TARGET: {"in_use": True, "mandatory": True}})
    assert get_ml_review_policy(DIV) == {
        LEARNING_TASK: {"in_use": True, "mandatory": True}}
    assert mandatory_keys(DIV) == ("learning_task",)
