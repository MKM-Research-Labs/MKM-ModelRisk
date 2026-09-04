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
"""Tests for the AI System aggregate (domain core).

An AI System is a deployed use of a generative or agentic model. It is the third
record type built on the same machinery, so the tests that matter most are the ones
proving it has not drifted from a model where it must not: the governance half
carries a model's field names exactly, and every clause probe reads those names.
Drift there is silent — the record still works, and the audit simply stops
counting it.
"""
from __future__ import annotations

import pytest

from config.governance import MODEL_FIELD_SPECS
from config.governance._ai import AI_SYSTEM_QUESTION_LIST
from config.governance._ai_system import (AGENT_TOOLS_COLLECTION,
                                          AI_REVIEW_QUESTIONS_COLLECTION,
                                          AI_SYSTEM_FIELD_SPECS)
from src.governance.ai_system import (add_collection_item, get_ai_system,
                                      list_ai_systems, rebuild_ai_system_view,
                                      register_ai_system, remove_collection_item,
                                      retire_ai_system, update_ai_system_field,
                                      update_collection_item)
from src.governance.errors import DomainError

_MINIMUM = {"name": "Client mail summariser", "division": "Risk",
            "owner": "David K Kelly",
            "use_case": "Summarises inbound client correspondence for the desk. "
                        "Not to be used to answer clients directly.",
            "deployment_pattern": "Retrieval-augmented (RAG)"}


def _register(ai_system_id="AIS-0001", **overrides):
    register_ai_system(ai_system_id=ai_system_id, fields={**_MINIMUM, **overrides},
                       actor="admin")
    rebuild_ai_system_view()
    return ai_system_id


def _data(ai_system_id="AIS-0001"):
    """Read through the projection, rebuilt first.

    Deliberately not reading the aggregate directly: the screens and the audit both
    read the view, so a test that skipped it could pass against a projection that
    never folded the event.
    """
    rebuild_ai_system_view()
    return get_ai_system(ai_system_id)["data"]


# --- The reason this record type looks the way it does ----------------------

def test_the_governance_half_uses_a_models_field_names_exactly():
    """The load-bearing invariant. Every clause probe in the completeness audit is
    a field-name lambda over one population, so an AI System is counted only for
    as long as these names match a model's. A rename here does not fail loudly —
    the audit just quietly stops counting AI Systems, which is the worst way for
    this to break."""
    shared = ("division", "line_of_business", "name", "short_name", "description",
              "tier", "tier_rationale", "materiality", "materiality_rationale",
              "complexity", "complexity_rationale", "rating_rationale", "rag_rating",
              "owner", "peer_reviewer", "model_owner_role", "status", "review_status",
              "lifecycle_stage", "validation_status", "version", "review_frequency",
              "last_review_date", "validation_date", "recertification_date",
              "next_review_date", "mrc_signoff_date", "mrc_signoff_meeting",
              "monitoring_approach", "unit_tests", "integration_tests",
              "benchmark_tests", "repo_location", "codebase")
    for field in shared:
        assert field in AI_SYSTEM_FIELD_SPECS, f"{field} missing from the AI System"
        assert field in MODEL_FIELD_SPECS, f"{field} is not a model field"


def test_it_does_not_carry_what_belongs_to_a_trained_model():
    """Nobody in the firm fitted this. An estimator or a training run here would be
    a field with no honest answer."""
    for field in ("estimator", "estimator_version", "training_runs", "estimator_rationale"):
        assert field not in AI_SYSTEM_FIELD_SPECS


# --- Registration -----------------------------------------------------------

def test_register_records_the_minimum():
    _register()
    data = _data()
    assert data["name"] == "Client mail summariser"
    assert data["deployment_pattern"] == "Retrieval-augmented (RAG)"


def test_deployment_pattern_is_required():
    """Not arbitrary: it decides which of the agentic risks apply at all, and the
    AI clause probes find their population by it. A record without one cannot be
    triaged and would be invisible to those probes."""
    with pytest.raises(DomainError):
        register_ai_system(ai_system_id="AIS-0009",
                           fields={k: v for k, v in _MINIMUM.items()
                                   if k != "deployment_pattern"}, actor="admin")


def test_registering_twice_is_refused():
    _register()
    with pytest.raises(DomainError):
        register_ai_system(ai_system_id="AIS-0001", fields=_MINIMUM, actor="admin")


def test_an_unknown_field_is_refused():
    with pytest.raises(DomainError):
        register_ai_system(ai_system_id="AIS-0002",
                           fields={**_MINIMUM, "temperature": "0.7"}, actor="admin")


def test_a_choice_field_rejects_a_value_outside_its_vocabulary():
    with pytest.raises(DomainError):
        register_ai_system(ai_system_id="AIS-0003",
                           fields={**_MINIMUM, "hosting": "Somebody's laptop"},
                           actor="admin")


def test_registration_seeds_the_ai_questionnaire():
    """Its own set, not the ML one: not a single ML question is answerable about a
    model the firm did not train."""
    _register()
    asked = _data()[AI_REVIEW_QUESTIONS_COLLECTION]
    assert len(asked) >= 10
    topics = {q["short_label"] for q in asked}
    assert {"Data Egress", "Agency and Authority", "Hallucination Exposure"} <= topics
    assert "Training Data" not in topics


# --- The reference lists ----------------------------------------------------

def test_the_foundation_model_list_is_open_until_it_is_curated():
    """The opposite of what "strict_reference" suggests, so it is pinned here.

    The list ships empty on purpose -- which models a firm has approved is a fact
    about their procurement, not something we can guess -- and an empty list is not
    enforced. So the field is open on day one and closes as soon as the institution
    records its first approved model. A register nobody can file a record into is
    worse than one that tightens later, but the control arrives with the curation
    rather than with the code, and that is worth knowing.
    """
    from src.governance.reference import add_option

    register_ai_system(ai_system_id="AIS-0101",
                       fields={**_MINIMUM, "foundation_model": "Nobody-Approved-This"},
                       actor="admin")

    add_option(list_name="foundation_model", fields={"value": "Approved-1"}, actor="admin")
    with pytest.raises(DomainError):
        register_ai_system(ai_system_id="AIS-0102",
                           fields={**_MINIMUM, "foundation_model": "Still-Not-Approved"},
                           actor="admin")
    register_ai_system(ai_system_id="AIS-0103",
                       fields={**_MINIMUM, "foundation_model": "Approved-1"}, actor="admin")


# --- Editing and retiring ---------------------------------------------------

def test_a_field_can_be_edited_and_the_view_follows():
    _register()
    update_ai_system_field(ai_system_id="AIS-0001", field="pinned_version",
                           value="2026-04-01", actor="admin")
    rebuild_ai_system_view()
    assert _data()["pinned_version"] == "2026-04-01"


def test_a_retired_system_is_out_of_the_estate_but_not_out_of_the_log():
    _register()
    retire_ai_system(ai_system_id="AIS-0001", actor="admin")
    rebuild_ai_system_view()
    assert list_ai_systems() == []
    assert len(list_ai_systems(include_retired=True)) == 1
    with pytest.raises(DomainError):
        update_ai_system_field(ai_system_id="AIS-0001", field="hosting",
                               value="On-premise", actor="admin")


# --- The tool list ----------------------------------------------------------

def test_tools_are_recorded_one_at_a_time():
    """A collection rather than a paragraph, because the agentic controls are asked
    tool by tool and "what can this system reach" has to be a query."""
    _register(deployment_pattern="Agentic (tool-using)")
    add_collection_item(ai_system_id="AIS-0001", collection=AGENT_TOOLS_COLLECTION,
                        fields={"name": "payments.transfer",
                                "authority": "Initiates a payment up to 10,000",
                                "approval": "Always"}, actor="admin")
    tools = _data()[AGENT_TOOLS_COLLECTION]
    assert len(tools) == 1 and tools[0]["approval"] == "Always"

    update_collection_item(ai_system_id="AIS-0001", collection=AGENT_TOOLS_COLLECTION,
                           item_id=tools[0]["item_id"],
                           fields={"approval": "Above a threshold"}, actor="admin")
    assert _data()[AGENT_TOOLS_COLLECTION][0]["approval"] == "Above a threshold"

    remove_collection_item(ai_system_id="AIS-0001", collection=AGENT_TOOLS_COLLECTION,
                           item_id=tools[0]["item_id"], actor="admin")
    assert _data()[AGENT_TOOLS_COLLECTION] == []


# --- What this record type exists for ---------------------------------------

def test_the_agentic_risk_rows_only_bite_on_agentic_systems():
    """AIR-SEC-024 is about an agent exceeding its authority. A direct-prompting
    summariser has no authority to exceed, so scoring it against that row would
    manufacture a gap the institution cannot close and should not try to."""
    from src.governance.completeness.framework import coverage
    from config.governance._finos import FINOS_RISKS

    _register()   # retrieval-augmented, not agentic
    estate = [get_ai_system("AIS-0001")]
    rows = coverage([], estate, "2026-08-25", (), [])
    agentic = next(r for r in rows
                   if r["framework"] == FINOS_RISKS and r["ref"] == "AIR-SEC-024")
    assert agentic["total"] == 0
    assert "No applicable record on the register" in agentic["evidence"]


def test_filling_the_ai_fields_moves_the_finos_risk_rows():
    """The whole reason this record type was built. Nineteen risk rows read Not
    evidenced because no generative system could be registered; these are the ones
    a well-kept AI System record answers."""
    from src.governance.completeness.framework import coverage
    from config.governance import COVERAGE_ABSENT, COVERAGE_EVIDENCED
    from config.governance._finos import FINOS_RISKS

    def _row(estate, ref):
        rows = coverage([], estate, "2026-08-25", (), [])
        return next(r for r in rows
                    if r["framework"] == FINOS_RISKS and r["ref"] == ref)

    # Three rows have left this list as the record grew, and each for the same
    # reason: they stopped being answerable by filling in scalar fields.
    #
    #   AIR-OP-016  counted over the whole estate from fairness_assessments.
    #   AIR-OP-004  needs an evaluation as well as a description of grounding —
    #               "answers are drawn only from the retrieved documents" is what
    #               the team meant to build, not evidence it works.
    #   AIR-OP-006  needs a reproducibility check specifically.
    #
    # All three are exercised in their own tests (test_evaluations,
    # test_fairness_and_classification). What remains here is the set that a
    # well-filled record genuinely does evidence on its own.
    moved = ("AIR-OP-005", "AIR-OP-007", "AIR-OP-014",
             "AIR-OP-017", "AIR-SEC-010", "AIR-RC-001")

    _register()
    bare = [get_ai_system("AIS-0001")]
    for ref in moved:
        assert _row(bare, ref)["state"] == COVERAGE_ABSENT, ref

    for field, value in (
        ("grounding", "Answers are drawn only from the retrieved correspondence."),
        ("human_oversight", "Human reviews before action"),
        ("pinned_version", "2026-04-01"),
        ("version_policy", "Pinned, reviewed on a cycle"),
        ("output_variability", "Temperature 0; sampled answers compared weekly."),
        ("provider", "Acme Analytics"),
        ("hosting", "Private cloud deployment"),
        ("guardrails", "Retrieved content is fenced and never treated as instruction."),
        ("explainability_approach", "Every answer cites the paragraphs it used."),
        ("data_egress", "Confidential business data"),
        ("data_egress_basis", "Clause 14 of the master agreement; no training on our data."),
    ):
        update_ai_system_field(ai_system_id="AIS-0001", field=field, value=value,
                               actor="admin")
    rebuild_ai_system_view()

    filled = [get_ai_system("AIS-0001")]
    for ref in moved:
        assert _row(filled, ref)["state"] == COVERAGE_EVIDENCED, ref


def test_an_unassessable_row_stays_absent_however_well_kept_the_record_is():
    """The honest half. A perfectly completed AI System record still evidences
    nothing about MCP supply chain or agent state poisoning, and the table must
    keep saying so rather than rewarding a full form."""
    from src.governance.completeness.framework import coverage
    from config.governance import COVERAGE_ABSENT
    from config.governance._finos import FINOS_RISKS

    _register()
    estate = [get_ai_system("AIS-0001")]
    rows = coverage([], estate, "2026-08-25", (), [])
    for ref in ("AIR-SEC-026", "AIR-SEC-027", "AIR-SEC-008", "AIR-RC-023"):
        row = next(r for r in rows
                   if r["framework"] == FINOS_RISKS and r["ref"] == ref)
        assert row["state"] == COVERAGE_ABSENT
        assert row["evidence"].strip()


def test_an_event_the_aggregate_does_not_know_leaves_the_state_alone():
    """The fold ignores what it does not recognise, rather than raising.

    A stream is replayed by every read, and it carries whatever the aggregate has
    ever emitted. An unknown type has to be a no-op or a single retired event kind
    would make the record unreadable for good — which, in an append-only log, is
    not a thing that can be undone.
    """
    from src.governance.ai_system._state import apply, initial_state

    state = initial_state()
    assert apply(state, "SomethingFromALaterVersion", {"any": "payload"}) is state
