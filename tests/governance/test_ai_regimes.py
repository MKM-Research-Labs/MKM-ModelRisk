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
"""Regulatory regimes as configuration against the shared core's contract.

Two claims, and the first is the one the phase exists to prove: a regime is DATA. If
adding one needs a source change, regimes are not configuration and an institution
cannot add the one their supervisor cares about.

The second is that applicability is derived from the record and not ticked. "Which
regimes apply to this system" has a right answer given where it is used and what it
does; a checkbox is an assertion nobody can check.
"""
from __future__ import annotations

from config.governance import _ai_regimes as regimes_config
from config.governance._ai_regimes import (AI_REGIMES, EU_AI_ACT, MARKETS_FIELD,
                                           NIST_AI_600_1, PRA_SS1_23, REGIME_COVERAGE,
                                           regimes_for)
from config.governance._ai_system import AI_SYSTEM_FIELD_SPECS
from config.governance._frameworks import FRAMEWORK_COVERAGE, FRAMEWORK_NOTES
from src.governance.completeness.framework import DECLARED, PROBES, coverage, tally

_ROWS = [{"record_id": "AIS-1"}]
_MODELS = [{"model_id": "AIS-1", "data": {"owner": "A", "peer_reviewer": "B"}}]


def _names(applicable):
    return [r["name"] for r in applicable]


# --- Applicability follows the record -----------------------------------------

def test_regime_applicability_follows_record_fields():
    """An EU-deployed system picks up the Act; a system that never leaves the US does
    not. The Act's own test is where a system is placed on the market or used, not
    where the firm is domiciled."""
    in_eu = regimes_for({MARKETS_FIELD: ["European Union", "United States"]})
    assert EU_AI_ACT in _names(in_eu)

    us_only = regimes_for({MARKETS_FIELD: ["United States"]})
    assert EU_AI_ACT not in _names(us_only)
    assert PRA_SS1_23 not in _names(us_only)


def test_a_system_serving_several_markets_picks_up_each_regime():
    """Multi-valued, so a match is an intersection: serving the EU and the UK is in
    scope of both, which is how the instruments work."""
    both = _names(regimes_for({MARKETS_FIELD: ["European Union", "United Kingdom"]}))
    assert EU_AI_ACT in both and PRA_SS1_23 in both


def test_a_regime_with_no_market_condition_applies_everywhere():
    """NIST's Profile is voluntary guidance the firm adopts, not a jurisdictional
    obligation, so it is not gated on where the system is used."""
    assert NIST_AI_600_1 in _names(regimes_for({}))
    assert NIST_AI_600_1 in _names(regimes_for({MARKETS_FIELD: ["Rest of world"]}))


def test_every_regime_states_why_it_applies():
    """A compliance officer has to be able to disagree on the facts rather than on the
    conclusion."""
    for applicable in regimes_for({MARKETS_FIELD: ["European Union", "United Kingdom"]}):
        assert applicable["because"].strip()


def test_the_record_carries_the_field_applicability_turns_on():
    spec = AI_SYSTEM_FIELD_SPECS[MARKETS_FIELD]
    assert spec["type"] == "multichoice", "a system usually serves more than one market"
    assert spec.get("reference"), "which markets a firm serves is an admin list"


# --- The contract proof --------------------------------------------------------

def test_a_fictional_regime_added_purely_in_config_appears_in_coverage(monkeypatch):
    """Add a regime nobody has heard of, in config alone, and it reports.

    This is the phase's whole claim. If it needs a source change, regimes are not
    configuration and an adopter cannot add the instrument their own supervisor cares
    about.
    """
    fictional = {
        "name": "Republic of Fiction AI Ordinance 2031",
        "applies_when": {MARKETS_FIELD: ("Republic of Fiction",)},
        "because": "Used in the Republic of Fiction.",
        "clauses": (("s.1", "Registration of automated systems", "inventory",
                     "Every registered record."),),
    }
    monkeypatch.setattr(regimes_config, "AI_REGIMES", AI_REGIMES + (fictional,))
    monkeypatch.setattr("config.governance._frameworks.FRAMEWORK_COVERAGE",
                        FRAMEWORK_COVERAGE + ((fictional["name"], fictional["clauses"]),))
    monkeypatch.setattr("src.governance.completeness.framework.FRAMEWORK_COVERAGE",
                        FRAMEWORK_COVERAGE + ((fictional["name"], fictional["clauses"]),))

    assert fictional["name"] in _names(
        regimes_for({MARKETS_FIELD: ["Republic of Fiction"]}))

    reported = coverage(_ROWS, _MODELS, "2026-09-05", framework=fictional["name"])
    assert [c["ref"] for c in reported] == ["s.1"]
    assert reported[0]["state"], "the fictional clause was measured by the shared engine"


# --- Registered like everything else ------------------------------------------

def test_the_regimes_report_through_the_same_engine():
    """Same shape, same engine, same row format — a regime differs from a framework in
    WHERE it applies, not in how it is counted."""
    names = [name for name, _ in FRAMEWORK_COVERAGE]
    for regime in (EU_AI_ACT, PRA_SS1_23, NIST_AI_600_1):
        assert regime in names

    clauses = coverage(_ROWS, _MODELS, "2026-09-05", framework=EU_AI_ACT)
    framework_row = coverage(_ROWS, _MODELS, "2026-09-05",
                             framework="ISO 31000:2018")[0]
    assert set(clauses[0]) == set(framework_row)


def test_every_regime_clause_names_a_probe_the_engine_knows():
    for name, clauses in REGIME_COVERAGE:
        for ref, title, probe, note in clauses:
            assert probe in PROBES or probe in DECLARED, \
                f"{name} {ref} names unknown probe {probe}"
            assert title.strip() and note.strip(), f"{name} {ref} is not explained"


def test_each_regime_disclaims_conformity():
    for regime in (EU_AI_ACT, PRA_SS1_23, NIST_AI_600_1):
        assert "the firm's own assessment" in FRAMEWORK_NOTES[regime]


def test_tally_scopes_to_one_regime():
    counts = tally(coverage(_ROWS, _MODELS, "2026-09-05"), EU_AI_ACT)
    assert counts["clauses"] == len(dict(REGIME_COVERAGE)[EU_AI_ACT])


def test_an_unassessed_act_class_is_not_counted_as_a_classification():
    """"Not assessed" is the absence of the assessment, not a class — and Art. 6 is the
    article a supervisor is most likely to ask the firm to justify."""
    unassessed = [{"model_id": "A", "data": {
        "eu_ai_act_class": "Not assessed", "eu_ai_act_rationale": "",
        "deployment_pattern": "Direct prompting"}}]
    row = next(c for c in coverage([{"record_id": "A"}], unassessed, "2026-09-05",
                                   framework=EU_AI_ACT) if c["ref"] == "Art. 6")
    assert row["met"] == 0
