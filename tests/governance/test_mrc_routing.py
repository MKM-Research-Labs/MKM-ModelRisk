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
"""Committee routing: how far up a record has to go, and why.

The rule these tests exist to hold is that routing gained INPUTS and not a second
committee track. An escalated AI System goes to the institution's own company
committee, not to an "AI committee" beside it — a parallel track is how AI governance
ends up somewhere the model risk function does not read.
"""
from __future__ import annotations

import pytest

from config.governance import VALID_MRC_LEVELS
from config.governance import _mrc_routing as routing_config
from config.governance._mrc_routing import LEVEL_ORDER, ROUTING_INPUTS, at_least
from src.governance.mrc import route
from src.web._signoff_subject import SUBJECTS

_REFS = {"mrc": [
    {"value": "MRC-LOB", "level": "Line of Business", "scope_value": "PRS Platform",
     "name": "PRS Platform MRC"},
    {"value": "MRC-DIV", "level": "Division", "scope_value": "PhysicalRisk",
     "name": "PhysicalRisk Division MRC"},
    {"value": "MRC-CO", "level": "Company", "scope_value": "", "name": "Company MRC"},
]}
_ORG = {"division": "PhysicalRisk", "line_of_business": "PRS Platform"}


def _route(record_type, **fields):
    return route(record_type, {**_ORG, "tier": "3", **fields}, _REFS)


# --- One case per record type, and the case the plan singles out --------------

@pytest.mark.parametrize("record_type,fields,expected_level,expected_rule", [
    # Ordinary records of each type still go to the closest committee that covers them.
    ("model", {}, "Line of Business", "default"),
    ("ml_application", {}, "Line of Business", "default"),
    # An AI System does not: the estate is new and a line of business has nothing to
    # compare one against.
    ("ai_system", {"deployment_pattern": "Direct prompting"}, "Division", "ai_by_default"),
    # The case the plan singles out: agentic routes differently from direct prompting.
    ("ai_system", {"deployment_pattern": "Agentic (tool-using)"}, "Company", "agentic_ai"),
    ("ai_system", {"deployment_pattern": "Multi-agent"}, "Company", "agentic_ai"),
    # Rules that read a field every record type carries apply to every record type.
    ("model", {"tier": "1"}, "Company", "mission_critical"),
    ("ml_application", {"tier": "1"}, "Company", "mission_critical"),
    ("ai_system", {"tier": "1", "deployment_pattern": "Direct prompting"},
     "Company", "mission_critical"),
    ("model", {"materiality": "High"}, "Division", "high_materiality"),
    ("ml_application", {"materiality": "High"}, "Division", "high_materiality"),
    # Regulatory class outranks everything below it.
    ("ai_system", {"eu_ai_act_class": "High risk (Annex III)",
                   "deployment_pattern": "Direct prompting"}, "Company", "high_risk_ai"),
    ("ai_system", {"eu_ai_act_class": "Prohibited",
                   "deployment_pattern": "Direct prompting"}, "Company", "prohibited_ai"),
])
def test_routing_by_record_type_and_attributes(record_type, fields, expected_level,
                                               expected_rule):
    outcome = _route(record_type, **fields)
    assert outcome["level"] == expected_level
    assert outcome["rule"] == expected_rule


def test_an_escalated_record_says_what_it_would_otherwise_have_gone_to():
    """A record escalated past its own committee without a stated cause is one somebody
    quietly routes back. "Because it is agentic" is an argument a committee can reject;
    a silent escalation is only a surprise."""
    outcome = _route("ai_system", deployment_pattern="Agentic (tool-using)")
    assert outcome["escalated"] is True
    assert outcome["mrc"]["name"] == "Company MRC"
    assert outcome["instead_of"]["name"] == "PRS Platform MRC"
    assert "act" in outcome["because"]


def test_an_unescalated_record_is_not_reported_as_one():
    outcome = _route("model")
    assert outcome["escalated"] is False
    assert outcome["instead_of"] is None


# --- No second track ----------------------------------------------------------

def test_subjects_still_enumerates_five():
    """Routing gained inputs, not a track. A sixth subject would be an AI committee
    sitting beside the model risk one."""
    assert len(SUBJECTS) == 5
    assert {s.kind for s in SUBJECTS} == {"model", "product", "handoff",
                                          "ml_application", "ai_system"}


def test_every_route_lands_on_a_committee_the_institution_defined():
    """The rules raise a level within the existing hierarchy; they cannot invent a
    committee. Every outcome is one of the three in the fixture."""
    defined = {m["value"] for m in _REFS["mrc"]}
    for record_type in ("model", "ml_application", "ai_system"):
        for tier in ("1", "2", "3"):
            outcome = _route(record_type, tier=tier,
                             deployment_pattern="Agentic (tool-using)")
            assert outcome["mrc"]["value"] in defined


def test_the_levels_a_rule_may_require_are_the_ones_admin_offers():
    """A rule requiring a level no committee can be created at would never match."""
    assert set(LEVEL_ORDER) == set(VALID_MRC_LEVELS)


def test_escalation_prefers_the_closest_committee_that_is_senior_enough():
    assert at_least("Division") == ("Division", "Company")
    assert at_least(None) == LEVEL_ORDER
    # Required at Division, and a division committee exists, so it is not taken to the
    # company one as well.
    assert _route("ai_system", deployment_pattern="Direct prompting")["level"] == "Division"


def test_a_rule_that_escalates_into_a_vacuum_says_so_rather_than_reading_as_uncovered():
    """A firm with no company committee and an agentic system has a gap in its
    committee STRUCTURE, not a record filed in the wrong division. Reporting it as "no
    committee covers this" sends somebody to recreate the committee they already have.
    """
    only_division = {"mrc": [{"value": "MRC-DIV", "level": "Division",
                              "scope_value": "PhysicalRisk",
                              "name": "PhysicalRisk Division MRC"}]}
    outcome = route("ai_system",
                    {**_ORG, "tier": "3", "deployment_pattern": "Agentic (tool-using)"},
                    only_division)
    assert outcome["mrc"] is None
    assert outcome["blocked"] is True
    assert outcome["escalated"] is False, "nothing took it, so nothing escalated it"
    assert outcome["required_level"] == "Company"
    assert outcome["instead_of"]["name"] == "PhysicalRisk Division MRC"


def test_a_record_with_no_covering_committee_is_not_reported_as_blocked():
    """Nothing covers its org location at all — the original message, and a different
    problem from a structure with no senior committee."""
    outcome = route("model", {"division": "Nowhere", "line_of_business": "Nothing"},
                    {"mrc": []})
    assert outcome["blocked"] is False and outcome["instead_of"] is None


def test_a_record_with_no_covering_committee_routes_nowhere_rather_than_anywhere():
    outcome = route("model", {"division": "Nowhere", "line_of_business": "Nothing"},
                    {"mrc": []})
    assert outcome["mrc"] is None and outcome["level"] is None


# --- The R1 proof -------------------------------------------------------------

def test_routing_changes_from_config_alone(monkeypatch):
    """Rewrite the rules and routing moves, with no change under src/.

    This is the whole claim: an institution that wants its agentic systems handled by
    the division, or its Tier 2 records escalated, edits one table. If this test needs
    a source change to pass, the rules have stopped being data.
    """
    before = _route("ai_system", deployment_pattern="Agentic (tool-using)")
    assert before["level"] == "Company"

    monkeypatch.setattr(routing_config, "ROUTING_RULES", (
        {"name": "agentic_stays_local", "when": {"record_type": ("ai_system",)},
         "level": "Line of Business", "because": "this firm handles them locally"},
        {"name": "default", "when": {}, "level": None, "because": "as before"},
    ))

    after = _route("ai_system", deployment_pattern="Agentic (tool-using)")
    assert after["level"] == "Line of Business"
    assert after["rule"] == "agentic_stays_local"
    assert after["because"] == "this firm handles them locally"


def test_first_match_wins_so_the_order_is_the_policy(monkeypatch):
    """Ordered, and read top to bottom. Reordering the table changes the estate."""
    monkeypatch.setattr(routing_config, "ROUTING_RULES", (
        {"name": "first", "when": {"record_type": ("model",)}, "level": "Company",
         "because": "first"},
        {"name": "second", "when": {"record_type": ("model",)}, "level": "Division",
         "because": "second"},
        {"name": "default", "when": {}, "level": None, "because": "default"},
    ))
    assert _route("model")["rule"] == "first"


def test_every_rule_tests_only_fields_a_record_could_carry():
    """A condition naming a field nothing holds is a rule that never fires, and it
    would sit in the table looking like policy."""
    for rule in routing_config.ROUTING_RULES:
        for field in (rule.get("when") or {}):
            assert field in ROUTING_INPUTS, f"{rule['name']} tests unknown field {field}"
        assert rule["because"].strip(), f"{rule['name']} gives no reason"
        assert rule["level"] is None or rule["level"] in LEVEL_ORDER
