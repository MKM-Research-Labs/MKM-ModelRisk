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
"""How complete a train's evidence is, and what disqualifies it.

Computed, never set by hand. The states are named for what they are -- Incomplete /
Qualified / Complete -- and NOT Red / Amber / Green, because RAG on this platform is
the risk rating the committee signed off. A model can be Green on risk and Incomplete
on training, and a reader must be able to tell those two facts apart.
"""
from __future__ import annotations

import pytest

from config.governance import TRAINING_FIELD_SPECS, TRAINING_RUNS_COLLECTION
from config.governance._ml_training import (MANDATORY, TEST_EVALUATION_CAP,
                                            TRAINING_COMPLETE, TRAINING_INCOMPLETE,
                                            TRAINING_QUALIFIED)
from src.governance.ml_application import (add_collection_item, get_ml_application,
                                           rebuild_ml_application_view,
                                           register_ml_application,
                                           update_collection_item)
from src.governance.ml_application.training import applies, completeness

_MINIMUM = {"name": "Retail PD scorecard", "division": "Risk", "owner": "Dana",
            "estimator": "GradientBoostingClassifier", "use_case": "Ranks applicants."}

_GOOD_RATIONALE = ("Neighbouring parcels share a catchment and a storm event, so a "
                   "random split leaks the same event into both sides. Split by catchment.")


def _complete_train(**overrides) -> dict:
    """Every mandatory field populated, no qualification triggered."""
    train = {"fit_id": "TR-001", "learning_task": "Regression"}
    for key, spec in TRAINING_FIELD_SPECS.items():
        if spec["requirement"] == MANDATORY:
            train.setdefault(key, "recorded")
    train.update({"split_rationale": _GOOD_RATIONALE, "scaler_fit_point": "Train only",
                  "test_evaluations": "1", "reproduced_by": "Sam Okafor",
                  "reproduced_matched": "Yes"})
    train.update(overrides)
    return train


# --- the three states -------------------------------------------------------

def test_a_train_with_nothing_recorded_is_incomplete():
    c = completeness({"fit_id": "TR-001"})
    assert c["state"] == TRAINING_INCOMPLETE
    assert c["filled"] == 0


def test_a_fully_evidenced_train_is_complete():
    c = completeness(_complete_train())
    assert c["state"] == TRAINING_COMPLETE
    assert c["missing"] == [] and c["qualifications"] == []


@pytest.mark.parametrize("field", ["target_definition", "snapshot_id", "split_method"])
def test_a_gap_in_task_data_or_split_is_incomplete_not_qualified(field):
    """Sections A, B and C are the foundation: what it is for, what it was fitted on,
    and how it was split. A gap there makes everything below it unreadable, so it is
    not a qualification on otherwise-good evidence."""
    c = completeness(_complete_train(**{field: ""}))
    assert c["state"] == TRAINING_INCOMPLETE


def test_a_gap_later_on_is_qualified():
    c = completeness(_complete_train(rebuild_command=""))
    assert c["state"] == TRAINING_QUALIFIED
    assert "rebuild_command" in c["missing"]


# --- the qualifications -----------------------------------------------------

def test_a_scaler_fitted_on_the_full_dataset_is_called_out():
    """The reported test metric is inflated: the scaler has seen the test set."""
    c = completeness(_complete_train(scaler_fit_point="Full dataset"))
    assert c["state"] == TRAINING_QUALIFIED
    assert any("leaks" in q for q in c["qualifications"])


def test_a_one_word_split_rationale_does_not_count_as_an_argument():
    c = completeness(_complete_train(split_rationale="Random."))
    assert c["state"] == TRAINING_QUALIFIED
    assert any("too short" in q for q in c["qualifications"])


def test_a_hold_out_looked_at_too_often_has_become_a_validation_set():
    c = completeness(_complete_train(test_evaluations=str(TEST_EVALUATION_CAP + 1)))
    assert c["state"] == TRAINING_QUALIFIED
    assert any("validation set" in q for q in c["qualifications"])


def test_an_unverified_fit_is_qualified():
    """The field that turns the tab from assertion into evidence."""
    c = completeness(_complete_train(reproduced_by=""))
    assert any("nobody other than the developer" in q for q in c["qualifications"])


def test_a_reproduction_that_did_not_match_is_qualified():
    c = completeness(_complete_train(reproduced_matched="No"))
    assert any("did not match" in q for q in c["qualifications"])


def test_a_non_numeric_evaluation_count_does_not_crash_the_calculation():
    """A completeness figure that raises is worse than one that is generous."""
    assert completeness(_complete_train(test_evaluations="lots"))["state"] == TRAINING_COMPLETE


# --- conditionals -----------------------------------------------------------

def test_a_neural_field_is_not_asked_of_a_regression():
    assert not applies("epochs", {"learning_task": "Regression"})
    assert applies("epochs", {"learning_task": "Image"})


def test_a_classification_is_asked_for_its_base_rate():
    assert applies("target_distribution", {"learning_task": "Binary classification"})
    assert not applies("target_distribution", {"learning_task": "Clustering"})


def test_the_denominator_follows_the_task():
    """A regression is not marked down for lacking a loss curve it never had."""
    regression = completeness(_complete_train(learning_task="Regression"))["total"]
    image = completeness(_complete_train(learning_task="Image"))["total"]
    assert image > regression


def test_a_conditional_rule_matches_the_stored_task_not_its_label():
    """Renaming a learning task in Admin changes what the screen says, never what the
    evidence must contain."""
    assert applies("epochs", {"learning_task": "Sequence"})
    assert not applies("epochs", {"learning_task": "sequence models (renamed)"})


# --- it is derived, not stored ----------------------------------------------

def test_the_record_carries_the_figure_and_it_moves_when_the_train_does(tmp_path):
    register_ml_application(ml_application_id="MLA-1", fields=_MINIMUM, actor="admin")
    add_collection_item(ml_application_id="MLA-1", collection=TRAINING_RUNS_COLLECTION,
                        fields={"fit_id": "TR-001"}, actor="admin")
    rebuild_ml_application_view()
    before = (get_ml_application("MLA-1")["data"] or {})["training_completeness"]
    assert before["state"] == TRAINING_INCOMPLETE and before["filled"] == 0

    update_collection_item(ml_application_id="MLA-1", collection=TRAINING_RUNS_COLLECTION,
                           item_id="TR-001",
                           fields={"learning_task": "Regression", "snapshot_id": "sha256:ab"},
                           actor="admin")
    rebuild_ml_application_view()
    after = (get_ml_application("MLA-1")["data"] or {})["training_completeness"]
    assert after["filled"] == 2


def test_only_the_most_recent_train_is_scored():
    """Earlier trains are history. Re-scoring them would mark a record down for the
    state of a fit it has since replaced."""
    register_ml_application(ml_application_id="MLA-2", fields=_MINIMUM, actor="admin")
    for fit in ("TR-001", "TR-002"):
        add_collection_item(ml_application_id="MLA-2", collection=TRAINING_RUNS_COLLECTION,
                            fields={"fit_id": fit}, actor="admin")
    update_collection_item(ml_application_id="MLA-2", collection=TRAINING_RUNS_COLLECTION,
                           item_id="TR-002", fields={"snapshot_id": "sha256:cd"},
                           actor="admin")
    rebuild_ml_application_view()
    data = get_ml_application("MLA-2")["data"] or {}
    assert len(data[TRAINING_RUNS_COLLECTION]) == 2
    assert data["training_completeness"]["filled"] == 1
