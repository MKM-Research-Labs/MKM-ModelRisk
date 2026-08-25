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
"""A review cannot be completed while what the division requires is still blank.

The gate is on COMPLETION and nowhere else: recording evidence is never blocked,
because a barrier to writing evidence down is a barrier to evidence.
"""
from __future__ import annotations

import pytest

from config.governance import TRAINING_ITEM_SOURCE, policy_item_id
from src.governance.errors import DomainError
from src.governance.ml_application import (add_collection_item, register_ml_application,
                                           rebuild_ml_application_view,
                                           update_collection_item,
                                           update_ml_application_field)
from src.governance.ml_application.review_scope import COMPLETING_REVIEW_STATUS
from src.governance.ml_review_policy import (approve_ml_review_policy,
                                             propose_ml_review_policy)
from src.governance.reference import ensure_default_estimators

DIV = "PhysicalRisk"
INTENDED = policy_item_id(TRAINING_ITEM_SOURCE, "intended_use")
MLA = "MLA-0001"


def _ratify(policy):
    propose_ml_review_policy(division=DIV, policy=policy, actor="admin")
    approve_ml_review_policy(division=DIV, actor="chair")


def _register():
    ensure_default_estimators()
    register_ml_application(
        ml_application_id=MLA,
        fields={"name": "Retail PD scorecard", "division": DIV,
                "owner": "David K Kelly", "estimator": "GradientBoostingClassifier",
                "use_case": "Ranks applicants by PD."},
        actor="admin")
    rebuild_ml_application_view()


def _train(fields=None):
    item = add_collection_item(ml_application_id=MLA, collection="training_runs",
                               fields={"fit_id": "1.0"}, actor="admin")
    if fields:
        update_collection_item(ml_application_id=MLA, collection="training_runs",
                               item_id=item.payload["item_id"], fields=fields,
                               actor="admin")
    rebuild_ml_application_view()


def _complete():
    update_ml_application_field(ml_application_id=MLA, field="review_status",
                                value=COMPLETING_REVIEW_STATUS, actor="admin")


def test_recording_evidence_is_never_blocked_however_much_is_outstanding():
    """The gate must not stand between somebody and writing down what they know."""
    _ratify({INTENDED: {"in_use": True, "mandatory": True}})
    _register()
    _train()                                        # a train with nothing in it
    update_ml_application_field(ml_application_id=MLA, field="methodology",
                                value="Gradient boosting", actor="admin")
    update_collection_item(ml_application_id=MLA, collection="training_runs",
                           item_id="TR-001", fields={"coverage": "40 gauges"},
                           actor="admin")


def test_completing_the_review_is_refused_while_a_mandatory_item_is_blank():
    _ratify({INTENDED: {"in_use": True, "mandatory": True}})
    _register()
    _train()
    with pytest.raises(DomainError, match="Intended use"):
        _complete()


def test_the_refusal_names_what_is_missing_rather_than_counting_it():
    task = policy_item_id(TRAINING_ITEM_SOURCE, "learning_task")
    _ratify({INTENDED: {"in_use": True, "mandatory": True},
             task: {"in_use": True, "mandatory": True}})
    _register()
    _train()
    with pytest.raises(DomainError) as caught:
        _complete()
    message = str(caught.value)
    assert "Intended use" in message and "Learning task" in message
    assert "2 item(s)" in message


def test_filling_the_mandatory_items_lets_the_review_complete():
    _ratify({INTENDED: {"in_use": True, "mandatory": True}})
    _register()
    _train({"intended_use": "Flood probability for the PRS desk."})
    _complete()
    rebuild_ml_application_view()


def test_an_estate_that_requires_nothing_completes_freely():
    """The default: shipping the gate blocks nobody until somebody sets a standard."""
    _register()
    _train()
    _complete()


def test_switching_the_requirement_off_unblocks_a_stuck_review():
    """Decision 3 the other way round: the institution can always relent."""
    _ratify({INTENDED: {"in_use": True, "mandatory": True}})
    _register()
    _train()
    with pytest.raises(DomainError):
        _complete()
    _ratify({})                                     # ratify a policy requiring nothing
    _complete()


def test_a_requirement_that_does_not_apply_does_not_block():
    """A classifier is not held up for a field only a regression is asked."""
    dist = policy_item_id(TRAINING_ITEM_SOURCE, "target_distribution")
    _ratify({dist: {"in_use": True, "mandatory": True}})
    _register()
    _train({"learning_task": "Regression"})
    _complete()
