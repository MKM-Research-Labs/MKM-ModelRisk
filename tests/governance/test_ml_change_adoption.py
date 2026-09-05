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
"""ML Applications adopt the four-tier engine — and what that turned out to mean.

The spec and the plan both describe this step as replacing "the existing SR 11-7 /
SR 26-2-aligned change-management triggers", and estimate it as a migration with a
vocabulary change for every open change record.

**There were no triggers.** Nothing in config or src named a change class, a trigger or
a tier before the engine was built in 0.1 — the same kind of claim v0.3 made about the
monitoring library, which the plan itself had already corrected for. What existed was
``change_history.change_type``: free text, no vocabulary, and blank on 24 of the 25 rows
on the estate.

So adoption is not a replacement, it is a first fitting: the history column takes the
engine's vocabulary so there is ONE answer to "how far-reaching was this change", and
the register the engine drives is the same one every other record type uses. These
tests hold that, and hold the two things a migration would have needed and this did not.
"""
from __future__ import annotations

from config.governance._change import CHANGE_CLASSES, SUBJECT_WORKFLOWS
from config.governance._collections import COLLECTION_SPECS
from config.governance._ml_application import ML_APPLICATION_COLLECTION_SPECS
from src.governance.change import (classify_change, get_change, list_changes_for,
                                   propose_change, rebuild_change_view)
from src.governance.change._rules import classify


def _change_type_field(specs):
    return next(f for f in specs["change_history"]["fields"]
                if f["key"] == "change_type")


# --- One vocabulary, not two --------------------------------------------------

def test_change_history_uses_the_engine_vocabulary_and_no_other():
    """Two vocabularies for the severity of a change is exactly what "running
    alongside" meant, and one of them would have gone unread."""
    field = _change_type_field(COLLECTION_SPECS)
    assert field["type"] == "choice"
    assert tuple(field["options"]) == CHANGE_CLASSES


def test_every_record_type_that_logs_changes_uses_the_same_vocabulary():
    assert (_change_type_field(ML_APPLICATION_COLLECTION_SPECS)["options"]
            == _change_type_field(COLLECTION_SPECS)["options"])


def test_the_vocabulary_has_exactly_the_four_tiers():
    """A fifth would be a tier the engine cannot resolve a revalidation depth for."""
    assert len(CHANGE_CLASSES) == 4
    assert set(_change_type_field(COLLECTION_SPECS)["options"]) == set(CHANGE_CLASSES)


# --- ML Applications go through the engine ------------------------------------

def test_an_ml_application_is_a_subject_the_engine_classifies():
    assert SUBJECT_WORKFLOWS["ml_application"] == "ml"


def test_an_ml_application_change_classifies_and_resolves_an_ml_depth():
    """Full adoption means an ML Application's change is classified by the same engine
    a model's is, and costs what the ML workflow says it costs."""
    propose_change(change_id="CHG-ML-1", subject_type="ml_application",
                   subject_id="MLA-1", rationale="Swap the estimator.",
                   before={"estimator": "LogisticRegression"},
                   after={"estimator": "GradientBoostingClassifier"}, actor="admin")
    classify_change(change_id="CHG-ML-1", actor="admin")
    rebuild_change_view()

    recorded = get_change("CHG-ML-1")["data"]
    assert recorded["change_class"] == "Material"
    assert recorded["revalidation_depth"] == "validation_pack_refresh"


def test_the_ml_triggers_are_the_engines_triggers():
    """What used to be a per-record-type judgement is now the shared trigger table:
    swapping an estimator is Material for the same reason swapping a model's
    methodology is."""
    assert classify(subject_type="ml_application",
                    before={"estimator": "a"}, after={"estimator": "b"}) == "Material"
    assert classify(subject_type="ml_application",
                    before={"estimator_version": "1.0"},
                    after={"estimator_version": "1.1"}) == "Measurement"
    assert classify(subject_type="ml_application", before={"name": "a"},
                    after={"name": "b"}) == "Administrative"


def test_changes_are_listed_against_the_ml_application_they_concern():
    propose_change(change_id="CHG-ML-2", subject_type="ml_application",
                   subject_id="MLA-2", rationale="Rename.",
                   before={"name": "A"}, after={"name": "B"}, actor="admin")
    rebuild_change_view()
    assert [c["change_id"] for c in list_changes_for("ml_application", "MLA-2")] \
        == ["CHG-ML-2"]
    assert list_changes_for("ml_application", "MLA-1") != \
        list_changes_for("ml_application", "MLA-2")


# --- What a migration would have needed, and why this did not ------------------

def test_the_only_change_severity_vocabulary_is_the_engines():
    """The plan's ``test_every_legacy_trigger_maps_to_exactly_one_tier`` has nothing to
    range over: the only pre-existing vocabulary was free text, and free text has no
    members to map. Asserted as an absence so the next reader does not go looking for a
    mapping table that never existed.

    ``VALID_REVIEW_TRIGGERS`` is deliberately NOT one of these and must not be folded
    in. It answers "why is this review happening" — periodic, new version, owner
    change, MRC directed — which is a different question from "how far-reaching is this
    change". A new version may be Administrative or Material, and collapsing the two
    vocabularies would make that unsayable.
    """
    from config.governance import VALID_REVIEW_TRIGGERS
    assert not set(VALID_REVIEW_TRIGGERS) & set(CHANGE_CLASSES)

    field = _change_type_field(COLLECTION_SPECS)
    assert tuple(field["options"]) == CHANGE_CLASSES, "one severity vocabulary only"


def test_an_unclassified_change_is_a_legitimate_state_not_a_backfill_gap():
    """Propose and classify are two acts, deliberately: the tier is a decision somebody
    records, not a property of the proposal. So an open unclassified change is normal,
    and "no unclassified open change" is not an invariant a backfill could establish.
    """
    propose_change(change_id="CHG-ML-3", subject_type="ml_application",
                   subject_id="MLA-3", rationale="Pending review.",
                   before={"name": "A"}, after={"name": "B"}, actor="admin")
    rebuild_change_view()
    assert get_change("CHG-ML-3")["data"]["change_class"] == ""
