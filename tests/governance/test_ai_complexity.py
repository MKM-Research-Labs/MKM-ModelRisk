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
"""The AI complexity axis and the materiality × complexity grid (spec v0.5 §2.2, §3.8).

The tables are seeded defaults an adopter edits, so most of these tests hold the tables'
SHAPE rather than their values: every combination has a cell, intensity never falls as
either axis rises, and each band asks for at least what the band below it does. An edit
that breaks one of those fails here instead of quietly placing a system in a lower band.
"""
from __future__ import annotations

import itertools

from config.governance._ai_complexity import (AI_AUTONOMY_LEVELS, AI_COMPLEXITY_LEVELS,
                                              AI_COMPLEXITY_RULE, AI_USAGE_FREQUENCIES,
                                              GOVERNANCE_INTENSITIES, GRID_INTENSITY,
                                              GRID_MATERIALITY_LEVELS, GRID_UNPLACED,
                                              MODEL_CLASSES, MODEL_CLASS_BY_RECORD_TYPE)
from config.governance._ai_concepts import (AI_CONCEPT_NUMBERS, AI_CONCEPTS,
                                            AI_LIFECYCLE_PHASES, INTENSITY_CONCEPTS)
from config.governance._ai_triggers import TRIGGER_PROPERTIES
from src.governance.ai_system.complexity import (ai_complexity, grid_position,
                                                 required_concepts)


def _rank(levels, value):
    return levels.index(value)


def test_every_autonomy_and_frequency_pair_has_a_complexity():
    for pair in itertools.product(AI_AUTONOMY_LEVELS, AI_USAGE_FREQUENCIES):
        assert AI_COMPLEXITY_RULE[pair] in AI_COMPLEXITY_LEVELS
    assert len(AI_COMPLEXITY_RULE) == len(AI_AUTONOMY_LEVELS) * len(AI_USAGE_FREQUENCIES)


def test_complexity_never_falls_as_autonomy_or_frequency_rises():
    for (a, f), level in AI_COMPLEXITY_RULE.items():
        for a2, f2 in itertools.product(AI_AUTONOMY_LEVELS, AI_USAGE_FREQUENCIES):
            if (_rank(AI_AUTONOMY_LEVELS, a2) >= _rank(AI_AUTONOMY_LEVELS, a)
                    and _rank(AI_USAGE_FREQUENCIES, f2) >= _rank(AI_USAGE_FREQUENCIES, f)):
                assert (_rank(AI_COMPLEXITY_LEVELS, AI_COMPLEXITY_RULE[(a2, f2)])
                        >= _rank(AI_COMPLEXITY_LEVELS, level)), (a, f, a2, f2)


def test_every_grid_cell_has_an_intensity():
    for cell in itertools.product(GRID_MATERIALITY_LEVELS, AI_COMPLEXITY_LEVELS):
        assert GRID_INTENSITY[cell] in GOVERNANCE_INTENSITIES


def test_intensity_never_falls_as_materiality_or_complexity_rises():
    rank = GOVERNANCE_INTENSITIES.index
    for (m, c), band in GRID_INTENSITY.items():
        for m2, c2 in GRID_INTENSITY:
            if (_rank(GRID_MATERIALITY_LEVELS, m2) >= _rank(GRID_MATERIALITY_LEVELS, m)
                    and _rank(AI_COMPLEXITY_LEVELS, c2) >= _rank(AI_COMPLEXITY_LEVELS, c)):
                assert rank(GRID_INTENSITY[(m2, c2)]) >= rank(band), (m, c, m2, c2)


def test_each_band_asks_for_everything_the_band_below_does():
    for lower, higher in zip(GOVERNANCE_INTENSITIES, GOVERNANCE_INTENSITIES[1:]):
        assert set(INTENSITY_CONCEPTS[lower]) <= set(INTENSITY_CONCEPTS[higher])
    assert set(INTENSITY_CONCEPTS[GOVERNANCE_INTENSITIES[-1]]) == set(AI_CONCEPT_NUMBERS)


def test_concept_matrix_matches_the_practice_paper():
    by_number = {c["number"]: c for c in AI_CONCEPTS}
    assert AI_CONCEPT_NUMBERS == tuple(range(1, 10))
    assert set(by_number[2]["properties"]) == set(TRIGGER_PROPERTIES)
    assert set(by_number[6]["properties"]) == set(TRIGGER_PROPERTIES)
    assert by_number[3]["properties"] == ("correctness",)
    assert by_number[7]["properties"] == ("robustness",)
    assert "predictability" not in by_number[4]["properties"]
    for concept in AI_CONCEPTS:
        assert concept["phase"] in AI_LIFECYCLE_PHASES
        assert set(concept["properties"]) <= set(TRIGGER_PROPERTIES)
    # Every property rests on at least one concept, or a coverage view could never show it.
    covered = {p for c in AI_CONCEPTS for p in c["properties"]}
    assert covered == set(TRIGGER_PROPERTIES)


def test_record_types_map_onto_the_two_classes():
    assert set(MODEL_CLASS_BY_RECORD_TYPE.values()) == set(MODEL_CLASSES)
    assert MODEL_CLASS_BY_RECORD_TYPE["AISystem"] == "AI_SYSTEM"


def test_a_complete_record_is_placed():
    pos = grid_position({"materiality": "High", "ai_autonomy": "AGENT",
                         "ai_usage_frequency": "DAILY"})
    assert pos["placed"] is True
    assert pos["position"] == "High × High"
    assert pos["intensity"] == GRID_INTENSITY[("High", "High")]
    assert 6 in pos["concepts"]
    assert pos["missing"] == []


def test_a_record_missing_inputs_is_not_placed_and_says_why():
    pos = grid_position({"materiality": "Low", "ai_autonomy": ""})
    assert pos["placed"] is False
    assert pos["position"] == GRID_UNPLACED
    assert pos["intensity"] is None and pos["concepts"] == ()
    assert pos["missing"] == ["Autonomy", "Usage frequency"]


def test_an_unknown_value_is_not_given_a_cell():
    pos = grid_position({"materiality": "Severe", "ai_autonomy": "AGENT",
                         "ai_usage_frequency": "DAILY"})
    assert pos["placed"] is False
    assert pos["missing"] == ["a grid cell for these values"]
    assert ai_complexity("AGENT", "HOURLY") is None


def test_trajectory_governance_is_asked_of_agents_only():
    top = GOVERNANCE_INTENSITIES[-1]
    assert 6 in required_concepts(top, "AGENT")
    assert 6 not in required_concepts(top, "WORKFLOW")
    assert 6 not in required_concepts(top, "SINGLE_CALL")
    assert required_concepts(None, "AGENT") == ()
