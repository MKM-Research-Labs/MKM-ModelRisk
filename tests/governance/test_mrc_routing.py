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
"""Committee routing: which committee governs a record, and why.

**Every record is managed at the MRC it is assigned to.** A model, an ML Application
and an AI System are each assigned to a division and a line of business, and the most
specific committee covering that org location signs the record off. The MRC is the
firm's risk committee and is itself the escalation point — there is nothing above it
for routing to reach.

These tests exist because that was briefly not true. An escalation ladder added on
2026-09-05 raised mission-critical and agentic records to a company committee that this
firm does not have and was never meant to need. It blocked two live tier-1 models,
MKM-GH-001 and MKM-PR-001, which had routed to the PhysicalRisk Division MRC for
months: a rule invented for a new record type reached back and changed how existing
models were governed. Removed 2026-09-06.
"""
from __future__ import annotations

from config.governance import VALID_MRC_LEVELS
from config.governance._reference import MRC_LEVELS_CLOSEST_FIRST
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
_KINDS = ("model", "ml_application", "ai_system")


def _route(record_type, **fields):
    return route(record_type, {**_ORG, "tier": "3", **fields}, _REFS)


# --- The closest committee covering where the record sits ---------------------

def test_every_record_type_routes_to_the_closest_covering_committee():
    """Same org location, same committee — whatever the record is."""
    for kind in _KINDS:
        outcome = _route(kind)
        assert outcome["mrc"]["value"] == "MRC-LOB"
        assert outcome["level"] == "Line of Business"
        assert outcome["blocked"] is False


def test_a_record_with_no_line_of_business_committee_falls_back_to_its_division():
    """"Closest" is a fallback, not a requirement: a record whose line of business has
    no committee is governed by its division's."""
    refs = {"mrc": [m for m in _REFS["mrc"] if m["value"] != "MRC-LOB"]}
    outcome = route("ai_system", {**_ORG, "tier": "3"}, refs)
    assert outcome["mrc"]["value"] == "MRC-DIV"
    assert outcome["level"] == "Division"


def test_no_attribute_of_a_record_changes_which_committee_governs_it():
    """Tier, materiality, deployment pattern and regulatory class describe how serious
    a record is and what it does. None of them decides WHERE it is governed — that is
    the org location, and only the org location.

    Written as one test over every combination that used to escalate, so the ladder
    cannot come back one rule at a time.
    """
    base = _route("model")["mrc"]["value"]
    for kind in _KINDS:
        for fields in ({"tier": "1"}, {"tier": 1}, {"materiality": "High"},
                       {"deployment_pattern": "Agentic (tool-using)"},
                       {"deployment_pattern": "Multi-agent"},
                       {"eu_ai_act_class": "High risk (Annex III)"},
                       {"eu_ai_act_class": "Prohibited"}):
            outcome = _route(kind, **fields)
            assert outcome["mrc"]["value"] == base, f"{kind} with {fields} routed away"
            assert outcome["blocked"] is False


def test_the_reason_travels_with_the_answer():
    """A screen has to be able to say why this committee, not merely which."""
    assert "division" in _route("model")["because"]


# --- Nothing covers it ---------------------------------------------------------

def test_a_record_no_committee_covers_routes_nowhere_rather_than_anywhere():
    outcome = route("model", {"division": "Nowhere", "line_of_business": "Nothing"},
                    {"mrc": []})
    assert outcome["mrc"] is None
    assert outcome["level"] is None
    assert outcome["blocked"] is True


def test_blocked_means_nothing_covers_it_and_nothing_else():
    """The one remaining cause. It used to also mean "a committee covers this but is
    not senior enough", which was a state only the escalation ladder could produce."""
    covered = _route("ai_system", deployment_pattern="Agentic (tool-using)")
    assert covered["blocked"] is False


# --- No second track ------------------------------------------------------------

def test_subjects_still_enumerates_five():
    """A sixth subject would be an AI committee sitting beside the model risk one."""
    assert len(SUBJECTS) == 5
    assert {s.kind for s in SUBJECTS} == {"model", "product", "handoff",
                                          "ml_application", "ai_system"}


def test_every_route_lands_on_a_committee_the_institution_defined():
    """Routing resolves to a committee the institution actually created in Admin; it
    cannot invent one."""
    defined = {m["value"] for m in _REFS["mrc"]}
    for kind in _KINDS:
        for tier in ("1", "2", "3"):
            assert _route(kind, tier=tier)["mrc"]["value"] in defined


def test_the_levels_searched_are_the_ones_admin_offers():
    """A level no committee can be created at would never match."""
    assert set(MRC_LEVELS_CLOSEST_FIRST) == set(VALID_MRC_LEVELS)


def test_the_search_order_is_most_specific_first():
    """The order is the policy: it is what makes "closest" mean closest."""
    assert MRC_LEVELS_CLOSEST_FIRST == ("Line of Business", "Division", "Company")
