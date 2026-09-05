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
"""Operate and measure: trajectories, trigger thresholds, and the failure-mode register.

Three tests here carry the phase, and each guards an absence or an independence rather
than a calculation:

  * trajectory scoring is skipped for a system that cannot act, derived from the
    deployment pattern and never from a second stated label;
  * the four trigger thresholds move independently, because a single severity applied
    to all four cannot express where the exposure actually sits;
  * the failure-mode register has NO mitigation status, which is the easiest thing in
    the plan to reintroduce by accident.
"""
from __future__ import annotations

import pytest

from config.governance._ai import DEPLOYMENT_PATTERNS
from config.governance._ai_ace import (ACE_ANCHORS, ACE_DIMENSIONS,
                                       ACE_SCALE, ACE_THRESHOLDS,
                                       below_threshold)
from config.governance._ai_failure_modes import (FAILURE_MODE_COLLECTION,
                                                 FORBIDDEN_FAILURE_MODE_FIELDS)
from config.governance._ai_system import AI_SYSTEM_COLLECTION_SPECS
from config.governance._ai_triggers import (DEFAULT_THRESHOLDS_BY_TIER,
                                            TRIGGER_PROPERTIES, default_thresholds)
from config.governance._ml_application import ML_APPLICATION_COLLECTION_SPECS
from src.governance.ai_system import (add_collection_item, get_ai_system,
                                      failure_modes_for_risk,
                                      rebuild_ai_system_view,
                                      rebuild_failure_mode_register_view,
                                      register_ai_system, set_trigger_threshold)
from src.governance.ai_system.trajectory import (AGENTIC_PATTERNS,
                                                 NON_AGENTIC_PATTERNS,
                                                 SKIPPED_NOT_AGENTIC, edit_distance,
                                                 score_trajectory)
from src.governance.errors import DomainError

_MINIMUM = {"name": "Claims triage agent", "division": "Risk", "owner": "A",
            "use_case": "Triages claims.", "deployment_pattern": "Agentic (tool-using)"}


def _register(ai_system_id="AIS-1", **overrides):
    register_ai_system(ai_system_id=ai_system_id, fields={**_MINIMUM, **overrides},
                       actor="admin")
    rebuild_ai_system_view()
    return ai_system_id


# --- 4.3 Trajectory scoring ---------------------------------------------------

def test_trajectory_scoring_skipped_for_direct_prompting():
    for pattern in NON_AGENTIC_PATTERNS:
        outcome = score_trajectory({"deployment_pattern": pattern}, ["a"], ["a"])
        assert outcome["applies"] is False
        assert outcome["status"] == SKIPPED_NOT_AGENTIC
        assert outcome["distance"] is None, "a skipped score reports no number"


def test_trajectory_scoring_applies_where_the_system_can_act():
    for pattern in AGENTIC_PATTERNS:
        outcome = score_trajectory({"deployment_pattern": pattern},
                                   ["lookup", "commit"], ["lookup", "commit"])
        assert outcome["applies"] is True and outcome["similarity"] == 1.0


def test_every_deployment_pattern_is_accounted_for():
    """A pattern added to config that can act must be added to the agentic set. Without
    this, a new pattern would silently skip trajectory scoring."""
    assert set(AGENTIC_PATTERNS) | set(NON_AGENTIC_PATTERNS) == set(DEPLOYMENT_PATTERNS)
    assert not set(AGENTIC_PATTERNS) & set(NON_AGENTIC_PATTERNS)


def test_applicability_comes_from_the_pattern_not_a_stored_flag():
    """Two fields disagreeing about whether a system can act is the worst possible
    thing for them to disagree about."""
    lying = {"deployment_pattern": "Direct prompting", "is_agentic": True,
             "agentic": "yes"}
    assert score_trajectory(lying, ["a"], ["b"])["applies"] is False


def test_an_extra_tool_call_is_one_edit_away():
    """The route matters even when the answer is right: an agent that called something
    it should not have is one insertion from the expected path, and that is the finding.
    """
    assert edit_distance(["lookup", "commit"], ["lookup", "commit"]) == 0
    assert edit_distance(["lookup", "pay", "commit"], ["lookup", "commit"]) == 1
    assert edit_distance(["pay"], ["lookup", "commit"]) == 2


# --- 4.4 Trigger thresholds ---------------------------------------------------

def test_four_thresholds_are_independently_editable():
    """Setting one moves no other. A single severity applied to all four cannot say
    that a customer-facing system needs a tighter robustness bar than a
    predictability one, which is the distinction the spec is explicit about."""
    _register()
    set_trigger_threshold(ai_system_id="AIS-1", property_name="robustness",
                          threshold=0.99, fallback="Suspend the system", actor="admin")
    rebuild_ai_system_view()
    after_one = get_ai_system("AIS-1")["data"]["trigger_thresholds"]
    assert set(after_one) == {"robustness"}, "setting one threshold set another"

    set_trigger_threshold(ai_system_id="AIS-1", property_name="predictability",
                          threshold=0.60, fallback="Continue and note", actor="admin")
    rebuild_ai_system_view()
    after_two = get_ai_system("AIS-1")["data"]["trigger_thresholds"]
    assert after_two["robustness"]["threshold"] == 0.99, "the first threshold moved"
    assert after_two["predictability"]["threshold"] == 0.60
    assert after_two["robustness"]["fallback"] == "Suspend the system"


def test_a_threshold_carries_what_happens_when_it_is_breached():
    """A trigger with no stated consequence is a metric."""
    _register()
    with pytest.raises(DomainError, match="fallback must be one of"):
        set_trigger_threshold(ai_system_id="AIS-1", property_name="correctness",
                              threshold=0.9, fallback="shrug", actor="admin")


@pytest.mark.parametrize("bad", [-0.1, 1.5, "high"])
def test_a_threshold_is_a_proportion(bad):
    _register()
    with pytest.raises(DomainError):
        set_trigger_threshold(ai_system_id="AIS-1", property_name="correctness",
                              threshold=bad, fallback="Continue and note", actor="admin")


def test_tiering_informs_the_starting_point_rather_than_fixing_all_four():
    """Defaults differ BETWEEN properties within one tier — which is the whole point:
    if a tier set all four to one number, the four could not be argued separately."""
    for tier, defaults in DEFAULT_THRESHOLDS_BY_TIER.items():
        assert set(defaults) == set(TRIGGER_PROPERTIES)
        assert len(set(defaults.values())) > 1, f"tier {tier} sets one bar for all four"


def test_an_unrated_record_gets_the_strictest_defaults_not_the_loosest():
    """A record nobody has rated is one nobody has thought about, and the safe reading
    of that is not to relax the bar."""
    assert default_thresholds(None) == DEFAULT_THRESHOLDS_BY_TIER["1"]
    assert default_thresholds("not a tier") == DEFAULT_THRESHOLDS_BY_TIER["1"]


# --- 4.5 The failure-mode register --------------------------------------------

def test_register_entry_has_no_mitigation_status_field():
    """Asserting the ABSENCE. Whether a mitigation is in place is answered from the
    documents tagged against the record by the FINOS coverage view; a status column
    here would answer the same question from a different source, and two registers that
    disagree are worse than one.

    This is the easiest thing in the plan to reintroduce by accident, because a status
    column looks obviously useful on an empty register.
    """
    fields = {f["key"] for f in
              AI_SYSTEM_COLLECTION_SPECS[FAILURE_MODE_COLLECTION]["fields"]}
    for forbidden in FORBIDDEN_FAILURE_MODE_FIELDS:
        assert forbidden not in fields, f"a mitigation status crept back in: {forbidden}"


def test_an_entry_holds_what_is_specific_to_it():
    """The risk it realises, the mitigation meant to prevent it, what detects it, and
    where it falls back to — and nothing that is answered elsewhere."""
    fields = {f["key"] for f in
              AI_SYSTEM_COLLECTION_SPECS[FAILURE_MODE_COLLECTION]["fields"]}
    assert {"finos_risk", "finos_mitigation", "trigger", "fallback"} <= fields


def test_the_register_is_ai_systems_only():
    """The agentic security cluster it exists to hold — tool chain manipulation, MCP
    server compromise, state poisoning — are exposures of generative and agentic
    systems specifically."""
    assert FAILURE_MODE_COLLECTION not in ML_APPLICATION_COLLECTION_SPECS


def test_the_register_answers_which_systems_can_fail_this_way():
    """Read across the estate, not only down one record: that is the question a
    per-record list cannot answer."""
    _register("AIS-1")
    _register("AIS-2")
    for ai_system_id in ("AIS-1", "AIS-2"):
        add_collection_item(ai_system_id=ai_system_id,
                            collection=FAILURE_MODE_COLLECTION,
                            fields={"description": "A tool result is treated as an "
                                                   "instruction.",
                                    "finos_risk": "AIR-SEC-025",
                                    "finos_mitigation": "AIR-PREV-019",
                                    "trigger": "Tool call outside the declared set.",
                                    "fallback": "Human review every output"},
                            actor="admin")
    add_collection_item(ai_system_id="AIS-1", collection=FAILURE_MODE_COLLECTION,
                        fields={"description": "Credential read in passing.",
                                "finos_risk": "AIR-SEC-029"}, actor="admin")
    rebuild_failure_mode_register_view()

    exposed = failure_modes_for_risk("AIR-SEC-025")
    assert {e["ai_system_id"] for e in exposed} == {"AIS-1", "AIS-2"}
    assert {e["ai_system_id"] for e in failure_modes_for_risk("AIR-SEC-029")} == {"AIS-1"}


# --- 4.1 Anchored Continuous Evaluation ---------------------------------------

def test_every_point_on_the_scale_is_anchored():
    """A five-point scale with no anchors is five people's opinions of "good". The
    anchors are what let two reviewers disagree and resolve it."""
    assert set(ACE_ANCHORS) == set(ACE_SCALE)
    for point, anchor in ACE_ANCHORS.items():
        assert anchor.strip(), f"point {point} has no anchor"


def test_every_dimension_has_a_bar_and_a_note():
    assert set(ACE_THRESHOLDS) == set(ACE_DIMENSIONS)
    for bar in ACE_THRESHOLDS.values():
        assert bar in ACE_SCALE, "a bar off the scale can never be cleared"


def test_dimensions_are_scored_against_their_own_bar_and_never_averaged():
    """A mean of the four would let a strong tone score pay for a weak safety one,
    which is exactly the trade the thresholds exist to prevent."""
    polite_breach = {"faithfulness": 4.5, "completeness": 4.0, "safety": 4.2,
                     "tone": 5.0}
    assert below_threshold(polite_breach) == ["safety"]
    # Its mean is 4.4, comfortably above every individual bar — which is the point.
    assert sum(polite_breach.values()) / 4 > max(
        ACE_THRESHOLDS[d] for d in ACE_DIMENSIONS if d != "safety")


def test_safety_is_the_dimension_with_no_headroom():
    """An unsafe output is not a lesser kind of unhelpful one."""
    assert ACE_THRESHOLDS["safety"] == max(ACE_SCALE)


def test_an_unscored_dimension_is_not_reported_as_a_failure():
    """Not scored and scored badly are different findings."""
    assert below_threshold({"safety": 5}) == []
    assert below_threshold({}) == []
