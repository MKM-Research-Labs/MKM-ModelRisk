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
"""Property coverage (spec v0.5 §3.8, AIGov edition): which of the four properties an AI
System's evidence holds up, concept by concept, against the configuration in force.

Built on record dicts rather than the database: the view is a pure reading of a record,
and these tests pin what it reads each piece of evidence as.
"""
from __future__ import annotations

import pytest

from config.governance._ai_system import CONFIGURATION_FIELDS
from src.governance.ai_system._rules_baseline import manifest_digest
from src.governance.ai_system.complexity import grid_position
from src.governance.ai_system.coverage import property_coverage

_VALUES = {f: None for f in CONFIGURATION_FIELDS}
_SNAP = {"config_version": 1, "values": _VALUES}
_CAL = {"judge_ai_system_id": "J", "dimension": "tone", "within_baseline": True}


def _status(data, n, grid=None):
    cov = property_coverage(data, grid or {"placed": False})
    return next(c for c in cov["concepts"] if c["number"] == n)["status"]


def _live_record(**extra):
    """Every concept evidenced under configuration v1."""
    contents = {"config_version": 1}
    return {
        "ai_autonomy": "AGENT", "configuration_snapshots": [_SNAP],
        "run_traces": [{"run_id": "R1", "config_version": 1, "complete": True}],
        "evaluations": [{"passed": "Passed", "judge_ai_system_id": "J"}],
        "variability_envelopes": [{"status": "ok", "config_version": 1}],
        "monitoring_observations": [{"field": "pd"}], "judge_calibrations": [_CAL],
        "stress_test_runs": [{"config_version": 1, "passed": True, "suite_version": 1}],
        "trigger_thresholds": {p: {"threshold": 0.9} for p in
                               ("correctness", "consistency", "robustness",
                                "predictability")},
        "release_manifests": [{"release": "1.0", "contents": contents,
                               "digest": manifest_digest(contents)}],
        **extra}


def test_an_empty_record_evidences_nothing():
    cov = property_coverage({}, {"placed": False})
    assert {c["status"] for c in cov["concepts"]} == {"no evidence", "not applicable"}
    assert cov["held_to"] == "every applicable concept"
    assert all(p["status"] == "not evidenced" for p in cov["properties"].values())


def test_a_fully_evidenced_agent_rests_on_live_evidence_bar_its_trajectories():
    cov = property_coverage(_live_record(), {"placed": False})
    live = {c["number"] for c in cov["concepts"] if c["status"] == "live"}
    assert live == {1, 2, 3, 4, 5, 7, 8, 9}
    assert _status(_live_record(), 6) == "no evidence"
    # Robustness is advanced by 1, 2, 4, 6, 7, 8 — only 6 is missing.
    assert cov["properties"]["robustness"] == {"status": "partly evidenced",
                                               "live": [1, 2, 4, 7, 8], "gaps": [6]}


def test_trajectories_are_not_asked_of_a_system_that_cannot_act():
    data = _live_record(ai_autonomy="WORKFLOW")
    assert _status(data, 6) == "not applicable"
    cov = property_coverage(data, {"placed": False})
    assert all(p["status"] == "rests on live evidence" for p in cov["properties"].values())
    # Unclassified: the deployment pattern decides, as the older rule did.
    assert _status({"deployment_pattern": "Multi-agent"}, 6) == "no evidence"
    assert _status({"deployment_pattern": "Direct prompting"}, 6) == "not applicable"


def test_a_moved_configuration_makes_bound_evidence_stale():
    data = _live_record(foundation_model="a different model")
    for n in (1, 2, 4, 7, 9):
        assert _status(data, n) == "stale", n
    assert property_coverage(data, {"placed": False})["config_version"] is None


def test_evidence_from_an_older_snapshot_is_stale_not_absent():
    data = _live_record(configuration_snapshots=[{"config_version": 1, "values": {}},
                                                 {**_SNAP, "config_version": 2}])
    assert _status(data, 2) == "stale" and _status(data, 7) == "stale"
    assert _status(data, 1) == "live"


@pytest.mark.parametrize("n, override", [
    (2, {"run_traces": [{"run_id": "R1", "config_version": 1, "complete": False}]}),
    (3, {"evaluations": [{"passed": "Failed"}]}),
    (3, {"judge_calibrations": [{**_CAL, "within_baseline": False}]}),
    (4, {"variability_envelopes": [{"status": "too few runs", "config_version": 1}]}),
    (5, {"judge_calibrations": [{**_CAL, "within_baseline": False}]}),
    (7, {"stress_test_runs": [{"config_version": 1, "passed": False, "suite_version": 2,
                               "failed": ["ST-001"]}]}),
    (8, {"trigger_thresholds": {"correctness": {"threshold": 0.9}}}),
    (9, {"release_manifests": [{"release": "1.0", "contents": {"config_version": 1},
                                "digest": "tampered"}]}),
])
def test_evidence_that_says_something_unwelcome_is_failing(n, override):
    assert _status(_live_record(**override), n) == "failing"


def test_an_envelope_under_an_older_configuration_is_stale():
    data = _live_record(variability_envelopes=[{"status": "ok", "config_version": 0}])
    assert _status(data, 4) == "stale"


def test_monitoring_counts_observations_or_calibrations():
    assert _status(_live_record(judge_calibrations=[]), 5) == "live"
    assert _status(_live_record(monitoring_observations=[]), 5) == "live"


def test_a_placed_system_is_held_only_to_what_its_band_asks():
    data = _live_record(ai_autonomy="SINGLE_CALL", materiality="Low",
                        ai_usage_frequency="AD_HOC")
    grid = grid_position(data)
    assert grid["intensity"] == "Baseline"
    cov = property_coverage({**data, "stress_test_runs": [], "trigger_thresholds": {}},
                            grid)
    assert cov["held_to"] == "the concepts its grid band asks for"
    asked = {c["number"] for c in cov["concepts"] if c["asked"]}
    assert asked == {1, 2, 3, 9}
    # Robustness at Baseline rests on 1 and 2 only; missing stress tests do not count.
    assert cov["properties"]["robustness"]["status"] == "rests on live evidence"


def test_a_property_no_asked_concept_advances_says_so():
    data = _live_record(ai_autonomy="SINGLE_CALL")
    grid = {"placed": True, "concepts": (3,)}
    cov = property_coverage(data, grid)
    assert cov["properties"]["predictability"]["status"] == "not asked of this system"
    assert cov["properties"]["correctness"]["status"] == "rests on live evidence"
