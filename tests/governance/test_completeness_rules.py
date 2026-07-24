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
"""Unit tests for the pure completeness-audit scoring rules.

The arithmetic here is what an audit reader is asked to trust, so the tests
assert the numbers rather than only the shape: a severity that silently changes
because a weight moved is a finding re-banded without anyone deciding to.
"""
from __future__ import annotations

import pytest

from config.governance import (
    DOC_CATEGORIES,
    EVENT_PRESSURE_CAP,
    MODEL_FIELD_SPECS,
    SEVERITY_BANDS,
    TIER_WEIGHTS,
    UNRATED_MULTIPLIER,
    UNTIERED_WEIGHT,
)
from src.governance.completeness._rules import (
    audit_entity,
    band,
    event_pressure,
    rag_multiplier,
    staleness,
    tier_weight,
)

AS_OF = "2026-07-23"
NO_RISK = {"heatmap": {"rag": None}, "events_in_window": 0}


def _audit(data, *, risk=None, available=None, specs=None, docs=DOC_CATEGORIES):
    return audit_entity(
        entity_kind="Model", entity_id="M1", entity_name="Alpha", data=data,
        field_specs=MODEL_FIELD_SPECS if specs is None else specs,
        collection_specs={}, doc_categories=docs, risk=risk or NO_RISK,
        as_of=AS_OF, available=available)


def _gap(result, key):
    return next(g for g in result["gaps"] if g["key"] == key)


# --- escalation factors ----------------------------------------------------

@pytest.mark.parametrize("tier", [1, 2, 3])
def test_tier_weight_reads_the_configured_table(tier):
    assert tier_weight(tier) == TIER_WEIGHTS[tier]
    assert tier_weight(str(tier)) == TIER_WEIGHTS[tier]


def test_untiered_record_escalates_rather_than_damps():
    """The absent tier is itself the reason to look, so it must not score below
    the lowest real tier — that would bury unclassified models."""
    assert tier_weight(None) == UNTIERED_WEIGHT
    assert tier_weight("") > min(TIER_WEIGHTS.values())


def test_unrated_record_escalates_above_green():
    assert rag_multiplier(None) == UNRATED_MULTIPLIER
    assert rag_multiplier(None) > rag_multiplier("Green")
    assert rag_multiplier("Red") > rag_multiplier("Amber") > rag_multiplier("Green")


def test_event_pressure_rises_then_caps():
    assert event_pressure(0) == 1.0
    assert event_pressure(2) > event_pressure(1) > 1.0
    assert event_pressure(500) == EVENT_PRESSURE_CAP


def test_event_pressure_tolerates_missing_and_negative_counts():
    assert event_pressure(None) == 1.0
    assert event_pressure(-3) == 1.0


def test_staleness_only_applies_once_a_review_is_overdue():
    assert staleness("2027-01-01", AS_OF) == 1.0        # not yet due
    assert staleness(None, AS_OF) == 1.0                # none scheduled
    assert staleness("2026-07-20", AS_OF) > 1.0         # days overdue
    assert staleness("2024-01-01", AS_OF) > staleness("2026-06-01", AS_OF)


def test_staleness_ignores_unparseable_dates_rather_than_failing():
    assert staleness("not-a-date", AS_OF) == 1.0
    assert staleness("2026-01-01", "not-a-date") == 1.0


def test_bands_run_worst_first_and_bottom_out():
    assert band(99.0) == SEVERITY_BANDS[0][0]
    assert band(0.0) == SEVERITY_BANDS[-1][0]
    assert band(-1.0) == SEVERITY_BANDS[-1][0]


# --- gap detection ---------------------------------------------------------

def test_recorded_negative_answer_is_not_a_gap():
    """A recorded "No" is an answer. Scoring it as absent would push owners to
    leave the field blank rather than record an inconvenient truth."""
    result = _audit({"unit_tests": "No"})
    assert "unit_tests" not in {g["key"] for g in result["gaps"]}


def test_blank_and_whitespace_fields_are_gaps():
    result = _audit({"owner": "   ", "methodology": ""})
    assert {"owner", "methodology"} <= {g["key"] for g in result["gaps"]}


def test_seeded_collection_needs_answers_not_merely_entries():
    """The nine validation questions exist from registration, so presence proves
    nothing; only worked entries count."""
    seeded = {"validation_questions": [{"status": "Not Addressed"}] * 9}
    result = audit_entity(
        entity_kind="Model", entity_id="M1", entity_name="Alpha", data=seeded,
        field_specs={}, collection_specs={"validation_questions": {"label": "VQ"}},
        doc_categories=(), risk=NO_RISK, as_of=AS_OF)
    assert _gap(result, "validation_questions")["detail"] == "none recorded"


def test_part_worked_collection_scores_below_an_untouched_one():
    specs = {"validation_questions": {"label": "VQ"}}
    common = dict(entity_kind="Model", entity_id="M1", entity_name="Alpha",
                  field_specs={}, collection_specs=specs, doc_categories=(),
                  risk=NO_RISK, as_of=AS_OF)
    worked = audit_entity(data={"validation_questions": [
        {"status": "Addressed"}] * 8 + [{"status": "Not Addressed"}]}, **common)
    untouched = audit_entity(data={"validation_questions": [
        {"status": "Not Addressed"}] * 9}, **common)
    assert (_gap(worked, "validation_questions")["severity"]
            < _gap(untouched, "validation_questions")["severity"])


def test_evidence_categories_are_not_raised_against_a_clean_record():
    """A model with no events and no remediation should not collect two
    guaranteed findings for the evidence it has nothing to evidence."""
    keys = {g["key"] for g in _audit({})["gaps"]}
    assert "Event Evidence" not in keys
    assert "Remediation Evidence" not in keys


def test_evidence_category_is_raised_once_there_is_something_to_evidence():
    result = _audit({"operational_failure_events": [{"date": "2026-01-01"}]})
    assert "Event Evidence" in {g["key"] for g in result["gaps"]}


# --- documents recorded but absent -----------------------------------------

def _with_doc(category):
    return {"documents": [{"category": category, "filename": "f.pdf"}]}


def test_retrievable_document_closes_the_category():
    result = _audit(_with_doc("Core Documentation"), available=lambda d: True)
    assert "Core Documentation" not in {g["key"] for g in result["gaps"]}


def test_document_recorded_but_absent_is_its_own_finding():
    result = _audit(_with_doc("Core Documentation"), available=lambda d: False)
    gap = _gap(result, "Core Documentation")
    assert gap["kind"] == "document_broken"
    assert gap["detail"] == "recorded, file absent"


def test_broken_reference_outscores_a_category_never_populated():
    """Both leave the same hole, but the broken one also tells a reader of the
    register that evidence exists — the more serious misstatement."""
    broken = _gap(_audit(_with_doc("Core Documentation"), available=lambda d: False),
                  "Core Documentation")
    never = _gap(_audit({}), "Core Documentation")
    assert broken["severity"] > never["severity"]


def test_register_is_trusted_when_no_availability_check_is_supplied():
    result = _audit(_with_doc("Core Documentation"))
    assert "Core Documentation" not in {g["key"] for g in result["gaps"]}


# --- assembly --------------------------------------------------------------

def test_severity_is_the_product_of_the_published_factors():
    """The report tells a reader they can reproduce any severity by hand from
    the five printed numbers. This is that promise."""
    risk = {"heatmap": {"rag": "Red"}, "events_in_window": 3}
    gap = _gap(_audit({"tier": 1, "next_review_date": "2024-01-01"}, risk=risk),
               "validation_date")
    expected = (gap["criticality"] * gap["tier_weight"] * gap["rag_multiplier"]
                * gap["event_pressure"] * gap["staleness"])
    assert gap["severity"] == pytest.approx(expected, abs=1e-4)
    assert gap["band"] == band(gap["severity"])


def test_findings_are_ordered_worst_first():
    severities = [g["severity"] for g in _audit({})["gaps"]]
    assert severities == sorted(severities, reverse=True)


def test_every_finding_carries_an_instruction_and_a_target():
    for gap in _audit({})["gaps"]:
        assert gap["action"].strip().endswith(".")
        assert gap["sla_days"] > 0


def test_acronym_labels_survive_into_the_instruction():
    """An owner should not be handed "record rag rating" to decode."""
    action = _gap(_audit({}), "rag_rating")["action"]
    assert "RAG rating" in action


def test_completeness_is_one_when_nothing_is_asked_for():
    result = audit_entity(
        entity_kind="Model", entity_id="M1", entity_name="Alpha", data={},
        field_specs={}, collection_specs={}, doc_categories=(),
        risk=NO_RISK, as_of=AS_OF)
    assert result["completeness"] == 1.0
    assert result["gaps"] == []


def test_completeness_rises_as_the_record_is_filled_in():
    specs = {k: MODEL_FIELD_SPECS[k] for k in ("owner", "methodology", "tier")}
    empty = _audit({}, specs=specs, docs=())["completeness"]
    partial = _audit({"owner": "A. Person"}, specs=specs, docs=())["completeness"]
    full = _audit({"owner": "A. Person", "methodology": "GEV", "tier": 1},
                  specs=specs, docs=())["completeness"]
    assert empty < partial < full == 1.0


def test_completeness_weights_the_expensive_fields_more_heavily():
    """Filling in a cheap field must not buy the same credit as an expensive
    one, or a record can look complete while its important fields stay blank."""
    specs = {k: MODEL_FIELD_SPECS[k] for k in ("tier", "division")}
    expensive = _audit({"tier": 1}, specs=specs, docs=())["completeness"]
    cheap = _audit({"division": "Markets"}, specs=specs, docs=())["completeness"]
    assert expensive > cheap


def test_exempt_collection_raises_no_finding():
    """An empty remediation list means nothing is outstanding. Scoring it would
    penalise exactly the records with the cleanest history."""
    result = audit_entity(
        entity_kind="Model", entity_id="M1", entity_name="Alpha", data={},
        field_specs={}, collection_specs={"remediation_steps": {"label": "Remediation"}},
        doc_categories=(), risk=NO_RISK, as_of=AS_OF)
    assert result["gaps"] == []


def test_staleness_falls_through_when_the_ladder_has_no_matching_step(monkeypatch):
    """The shipped ladder bottoms at 0 days, so every overdue review matches a
    step. An adopter who removes that bottom rung must still get a defined
    answer rather than None — this guards that fall-through."""
    from src.governance.completeness import _rules
    monkeypatch.setattr(_rules, "STALENESS_STEPS", ((365, 1.20),))
    assert _rules.staleness("2026-07-20", AS_OF) == _rules.STALENESS_NONE


def test_fully_populated_collection_raises_no_finding():
    result = audit_entity(
        entity_kind="Model", entity_id="M1", entity_name="Alpha",
        data={"assumptions": [{"description": "x"}]},
        field_specs={}, collection_specs={"assumptions": {"label": "Assumptions"}},
        doc_categories=(), risk=NO_RISK, as_of=AS_OF)
    assert result["gaps"] == []
    assert result["completeness"] == 1.0


def test_placeholder_values_do_not_count_as_recorded():
    """A field holding "TBD" reads as filled to the register and as empty to a
    person. Scoring it as recorded lets a record certify itself complete on words
    that commit to nothing — the failure this audit exists to catch."""
    specs = {k: MODEL_FIELD_SPECS[k] for k in ("peer_reviewer",)}
    for value in ("TBD", "tbd", " N/A ", "--", "pending"):
        result = _audit({"peer_reviewer": value}, specs=specs, docs=())
        assert [g["key"] for g in result["gaps"]] == ["peer_reviewer"], value


def test_a_real_answer_is_still_recorded():
    specs = {k: MODEL_FIELD_SPECS[k] for k in ("peer_reviewer",)}
    assert _audit({"peer_reviewer": "A. Reviewer"}, specs=specs, docs=())["gaps"] == []


def test_history_category_is_never_an_owner_obligation():
    """History holds copies the platform files automatically when a Model Risk
    Document is issued; demanding it reports platform usage, not governance."""
    assert "History" not in {g["key"] for g in _audit({})["gaps"]}


def test_test_results_pack_closes_the_sub_test_categories():
    """The pack reports every unit and integration test with its assertions;
    three further uploads restating the same run close no real gap."""
    data = {"documents": [{"category": "Test Results", "filename": "t.pdf"}]}
    keys = {g["key"] for g in _audit(data, available=lambda d: True)["gaps"]}
    assert not ({"Unit Test", "Integration Test", "Benchmark Test"} & keys)


def test_sub_test_categories_are_raised_when_no_pack_exists():
    """A model with no testing evidence at all is still reported — the pack
    closes them, its absence does not."""
    keys = {g["key"] for g in _audit({})["gaps"]}
    assert {"Unit Test", "Integration Test", "Benchmark Test"} <= keys
