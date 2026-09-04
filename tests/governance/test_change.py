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
"""Tests for the Change aggregate: the four-tier classification engine.

Two properties carry the whole feature, and both are asserted here rather than left to
inspection. **Determinism** — the same proposal classifies the same way every time,
because a tier that drifted between readings would make the register worthless as
evidence. **Totality** — every class resolves a depth in every workflow, because a
change that classifies successfully and then names no depth tells nobody what to do.
"""
from __future__ import annotations

import pytest

from config.governance._change import (CHANGE_CLASSES, CHANGE_TRIGGERS,
                                       CHANGE_WORKFLOWS, DEFAULT_CHANGE_CLASS,
                                       REVALIDATION_DEPTH, REVALIDATION_DEPTHS,
                                       SUBJECT_WORKFLOWS, revalidation_depth_for,
                                       workflow_for)
from src.database import ConcurrencyError
from src.governance.change import (classify_change, get_change, list_changes,
                                   list_changes_for, propose_change,
                                   rebuild_change_view, supersede_change)
from src.governance.change._rules import classify, moved_fields
from src.governance.errors import DomainError


def _propose(change_id="CHG-001", subject_type="model", subject_id="M-001",
             after=None, **kwargs):
    propose_change(change_id=change_id, subject_type=subject_type,
                   subject_id=subject_id, rationale="Because the desk asked",
                   before=kwargs.pop("before", {"methodology": "OLS"}),
                   after={"methodology": "GBM"} if after is None else after,
                   actor="admin", **kwargs)
    return change_id


def _data(change_id="CHG-001"):
    """Read through the projection, rebuilt first — the screens read the view, so a
    test that skipped it could pass against a projection that never folded the event."""
    rebuild_change_view()
    return get_change(change_id)["data"]


# --- The two properties the feature rests on ---------------------------------

def test_classify_is_deterministic():
    """The same before/after pair, twice, is the same tier.

    Trivially true of the implementation as written, and asserted anyway: the
    temptation later is to let the tier depend on who is asking or on when — a
    Material change "downgraded because it was already reviewed" — and this is the
    test that fails when it does.
    """
    args = dict(subject_type="ai_system",
                before={"foundation_model": "claude-opus-4", "name": "Summariser"},
                after={"foundation_model": "claude-opus-5", "name": "Summariser II"},
                affected_artifacts=["benchmark_set"])
    assert classify(**args) == classify(**args) == "Material"


def test_every_class_resolves_a_depth_for_both_workflows():
    """The 4x2 matrix is total, and every depth it names is a defined one."""
    for change_class in CHANGE_CLASSES:
        for workflow in CHANGE_WORKFLOWS:
            depth = revalidation_depth_for(change_class, workflow)
            assert depth in REVALIDATION_DEPTHS, (change_class, workflow, depth)
    assert len(REVALIDATION_DEPTH) == len(CHANGE_CLASSES) * len(CHANGE_WORKFLOWS)


def test_the_two_workflows_differ_where_it_matters():
    """Shared engine, different consequence — the point of keying depth by workflow.

    If these ever coincide the workflows have been quietly merged, which is the one
    thing the AI and ML processes must not do.
    """
    assert (revalidation_depth_for("Material", "ml")
            != revalidation_depth_for("Material", "ai"))
    assert (revalidation_depth_for("Measurement", "ml")
            != revalidation_depth_for("Measurement", "ai"))
    assert (revalidation_depth_for("Administrative", "ml")
            == revalidation_depth_for("Administrative", "ai"))


def test_unknown_cell_raises():
    with pytest.raises(KeyError):
        revalidation_depth_for("Cosmetic", "ml")


# --- What triggers what ------------------------------------------------------

def test_severity_wins_over_position():
    """A rename plus a methodology swap is a methodology swap with a rename attached."""
    assert classify(subject_type="model",
                    before={"name": "A", "methodology": "OLS"},
                    after={"name": "B", "methodology": "GBM"}) == "Material"


def test_restating_a_value_is_not_a_change():
    """Sending a field back at its current value cannot inflate a tier."""
    assert moved_fields({"methodology": "OLS"}, {"methodology": "OLS"}) == ()
    assert classify(subject_type="model", before={"methodology": "OLS"},
                    after={"methodology": "OLS"}) == DEFAULT_CHANGE_CLASS


def test_a_field_absent_from_after_is_untouched():
    """A proposal describes what it moves; silence is not a request to clear."""
    assert moved_fields({"methodology": "OLS", "name": "A"}, {"name": "B"}) == ("name",)


def test_untriggered_field_falls_to_the_default():
    assert classify(subject_type="model", before={"description": "x"},
                    after={"description": "y"}) == DEFAULT_CHANGE_CLASS


def test_empty_proposal_is_the_default_class():
    assert classify(subject_type="model", before={}, after={}) == DEFAULT_CHANGE_CLASS


def test_triggers_are_scoped_to_the_record_type():
    """``estimator`` is Material on an ML Application and unknown to a model."""
    assert classify(subject_type="ml_application", before={"estimator": "a"},
                    after={"estimator": "b"}) == "Material"
    assert classify(subject_type="model", before={"estimator": "a"},
                    after={"estimator": "b"}) == DEFAULT_CHANGE_CLASS


def test_finos_taxonomy_bump_is_measurement_not_material():
    """The spec's own instruction (§9.5): a version bump is Measurement-class against
    the mapping engine, not Material against every record the engine mapped."""
    assert classify(subject_type="ai_system", before={}, after={},
                    affected_artifacts=["finos_taxonomy"]) == "Measurement"


def test_a_rerating_is_material_on_every_record_type():
    for subject_type in SUBJECT_WORKFLOWS:
        assert classify(subject_type=subject_type, before={"tier": "3"},
                        after={"tier": "1"}) == "Material"


def test_every_trigger_names_a_defined_class_and_record_type():
    """Dead data in the trigger table classifies nothing and is invisible until read."""
    for rule in CHANGE_TRIGGERS:
        assert rule["change_class"] in CHANGE_CLASSES
        for subject_type in rule.get("applies_to") or ():
            assert subject_type in SUBJECT_WORKFLOWS
        assert rule.get("fields") or rule.get("artifacts")


def test_workflow_for_declines_a_record_type_it_does_not_govern():
    """``None`` rather than a default: a Product has no revalidation depth to resolve."""
    assert workflow_for("model") == "ml"
    assert workflow_for("ai_system") == "ai"
    assert workflow_for("product") is None


# --- Through the log and back ------------------------------------------------

def test_propose_then_classify_round_trips():
    _propose()
    classify_change(change_id="CHG-001", actor="admin")
    data = _data()
    assert data["change_class"] == "Material"
    assert data["revalidation_depth"] == revalidation_depth_for("Material", "ml")
    assert data["subject_id"] == "M-001"
    assert data["superseded"] is False


def test_stale_version_conflicts():
    """A second write against a stale ``expected_version`` is refused.

    Reaching past the command to ``append_event`` is the point: the command reloads
    and so can never be stale, and what this proves is that the guard underneath it
    is armed — two sessions classifying the same proposal at once.
    """
    from src.database import append_event
    _propose()
    with pytest.raises(ConcurrencyError):
        append_event(aggregate_type="Change", aggregate_id="CHG-001",
                     event_type="ChangeSuperseded", payload={}, actor="admin",
                     expected_version=0)


def test_classifying_twice_is_refused():
    """The tier is evidence of a decision, not a recomputation."""
    _propose()
    classify_change(change_id="CHG-001", actor="admin")
    with pytest.raises(DomainError):
        classify_change(change_id="CHG-001", actor="admin")


def test_superseded_change_accepts_nothing_further():
    _propose()
    supersede_change(change_id="CHG-001", actor="admin")
    assert _data()["superseded"] is True
    with pytest.raises(DomainError):
        classify_change(change_id="CHG-001", actor="admin")
    with pytest.raises(DomainError):
        supersede_change(change_id="CHG-001", actor="admin")


def test_commands_against_a_missing_change_are_refused():
    with pytest.raises(DomainError):
        classify_change(change_id="CHG-404", actor="admin")
    with pytest.raises(DomainError):
        supersede_change(change_id="CHG-404", actor="admin")


def test_proposing_the_same_id_twice_is_refused():
    _propose()
    with pytest.raises(DomainError):
        _propose()


@pytest.mark.parametrize("kwargs,message", [
    ({"change_id": ""}, "change_id"),
    ({"subject_id": ""}, "subject_id"),
    ({"subject_type": "product"}, "not classified"),
])
def test_proposal_validation(kwargs, message):
    with pytest.raises(DomainError, match=message):
        _propose(**kwargs)


def test_a_proposal_needs_a_rationale():
    with pytest.raises(DomainError, match="rationale"):
        propose_change(change_id="CHG-009", subject_type="model", subject_id="M-001",
                       rationale="   ", before={}, after={"methodology": "GBM"},
                       actor="admin")


def test_a_proposal_must_move_something():
    with pytest.raises(DomainError, match="at least one"):
        _propose(after={})


# --- The register ------------------------------------------------------------

def test_the_register_filters_by_subject_and_by_open():
    _propose("CHG-001", subject_id="M-001")
    _propose("CHG-002", subject_id="M-002")
    _propose("CHG-003", subject_type="ai_system", subject_id="M-001")
    supersede_change(change_id="CHG-002", actor="admin")
    rebuild_change_view()

    assert [r["change_id"] for r in list_changes_for("model", "M-001")] == ["CHG-001"]
    assert [r["change_id"] for r in list_changes_for("ai_system", "M-001")] == ["CHG-003"]
    assert len(list_changes()) == 3
    assert [r["change_id"] for r in list_changes(include_superseded=False)] == \
        ["CHG-001", "CHG-003"]
    assert list_changes_for("model", "M-002", include_superseded=False) == []


def test_the_projection_carries_the_artifacts_and_the_movement():
    """What was asked for stays readable — a reader can see the proposal, not just its
    verdict."""
    _propose(after={"methodology": "GBM"}, affected_artifacts=["validation_pack"])
    data = _data()
    assert data["before"] == {"methodology": "OLS"}
    assert data["after"] == {"methodology": "GBM"}
    assert data["affected_artifacts"] == ["validation_pack"]
    assert data["rationale"] == "Because the desk asked"


def test_an_unhandled_event_does_not_break_the_fold():
    """An event type the fold does not know is ignored, not fatal. It stays in the log."""
    from src.database import append_event
    _propose()
    append_event(aggregate_type="Change", aggregate_id="CHG-001",
                 event_type="ChangeGarnished", payload={}, actor="admin")
    assert _data()["change_class"] == ""
