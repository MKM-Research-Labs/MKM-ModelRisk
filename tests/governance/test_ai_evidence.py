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
"""The run evidence an AI System records: trace references, stress-test runs, judge
calibration (config/governance/_ai_evidence.py; spec v0.5 §9.1, §9.3, AIGov edition).

Each verdict is the server's — completeness, pass/fail, agreement — and each record is
appended and never amended.
"""
from __future__ import annotations

import pytest

from src.governance.ai_system import (add_collection_item, get_ai_system,
                                      rebuild_ai_system_view, record_judge_calibration,
                                      record_run_trace, record_stress_test_run,
                                      register_ai_system, take_configuration_snapshot)
from src.governance.ai_system._rules_evidence import judge_reliance
from src.governance.ai_system.judges import judges_of
from src.governance.errors import DomainError

_HASH = "ab" * 32
_MIN = {"division": "Risk", "owner": "David K Kelly",
        "use_case": "Drafts the first pass of a credit memo.",
        "deployment_pattern": "Agentic (tool-using)"}


def _system(ai_system_id="AIS-0001", snapshot=True, **fields):
    register_ai_system(ai_system_id=ai_system_id,
                       fields={"name": ai_system_id, **_MIN, **fields}, actor="admin")
    if snapshot:
        take_configuration_snapshot(ai_system_id=ai_system_id, actor="admin")
    return ai_system_id


def _data(ai_system_id="AIS-0001"):
    rebuild_ai_system_view()
    return get_ai_system(ai_system_id)["data"]


def _trace(run_id="R1", contents=(), **kw):
    return record_run_trace(**{"ai_system_id": "AIS-0001", "run_id": run_id,
                               "trace_uri": f"otel://traces/{run_id}",
                               "content_hash": _HASH, "contents": list(contents),
                               "purpose": "Production sample", "actor": "admin", **kw})


# --- Traces --------------------------------------------------------------------------

def test_a_complete_single_call_trace_is_recorded_with_its_hash():
    _system(ai_autonomy="SINGLE_CALL")
    _trace(contents=["case_input", "model_snapshot", "controls_in_force", "output",
                     "parser_result"])
    trace = _data()["run_traces"][0]
    assert trace["complete"] is True and trace["missing"] == []
    assert trace["content_hash"] == _HASH and trace["config_version"] == 1


def test_an_agent_owes_more_and_an_incomplete_trace_is_recorded_as_such():
    _system(ai_autonomy="AGENT")
    _trace(contents=["case_input", "model_snapshot", "controls_in_force", "output",
                     "parser_result"])
    trace = _data()["run_traces"][0]
    assert trace["complete"] is False
    assert "step_graph" in trace["missing"] and "checks_retries_errors" in trace["missing"]


@pytest.mark.parametrize("override, message", [
    ({"content_hash": "not-a-hash"}, "SHA-256"),
    ({"content_hash": "zz" * 32}, "SHA-256"),
    ({"purpose": "Curiosity"}, "purpose must be one of"),
    ({"trace_uri": ""}, "run_id and trace_uri are required"),
    ({"contents": ["vibes"]}, "unknown trace content: vibes"),
])
def test_a_malformed_trace_is_refused(override, message):
    _system(ai_autonomy="WORKFLOW")
    with pytest.raises(DomainError, match=message):
        _trace(**override)


def test_a_run_is_referenced_once():
    _system(ai_autonomy="WORKFLOW")
    _trace()
    with pytest.raises(DomainError, match="already recorded"):
        _trace()


def test_a_trace_needs_autonomy_and_a_configuration_to_be_read_against():
    _system()
    with pytest.raises(DomainError, match="set the system's autonomy first"):
        _trace()
    _system("AIS-0002", snapshot=False, ai_autonomy="AGENT")
    with pytest.raises(DomainError, match="take a configuration snapshot first"):
        _trace(ai_system_id="AIS-0002")


# --- Stress tests --------------------------------------------------------------------

def _case(scenario, expected, category="ADVERSARIAL"):
    add_collection_item(ai_system_id="AIS-0001", collection="stress_test_cases",
                        fields={"scenario": scenario, "category": category,
                                "expected_response": expected}, actor="admin")


def _cases():
    return [c["item_id"] for c in _data()["stress_test_cases"]]


def test_a_run_is_judged_case_by_case_and_versions_the_suite_itself():
    _system()
    _case("Injected instruction in a retrieved filing", "REFUSE_ISOLATE")
    _case("Rating API times out", "RETRY", "OPERATIONAL")
    a, b = _cases()
    record_stress_test_run(ai_system_id="AIS-0001", occasion="Before release",
                           observed={a: "REFUSE_ISOLATE", b: "HOLD_ESCALATE"},
                           actor="admin")
    run = _data()["stress_test_runs"][0]
    assert run["suite_version"] == 1 and run["passed"] is False and run["failed"] == [b]
    record_stress_test_run(ai_system_id="AIS-0001", occasion="Scheduled",
                           observed={a: "REFUSE_ISOLATE", b: "RETRY"}, actor="admin")
    assert _data()["stress_test_runs"][1]["suite_version"] == 1
    _case("Poisoned vector store entry", "HOLD_ESCALATE")
    c = _cases()[2]
    record_stress_test_run(ai_system_id="AIS-0001", occasion="After a Material change",
                           observed={a: "REFUSE_ISOLATE", b: "RETRY", c: "HOLD_ESCALATE"},
                           actor="admin")
    third = _data()["stress_test_runs"][2]
    assert third["suite_version"] == 2 and third["passed"] is True


def test_a_run_must_cover_the_whole_suite_with_known_responses():
    _system()
    with pytest.raises(DomainError, match="no cases yet"):
        record_stress_test_run(ai_system_id="AIS-0001", occasion="Scheduled",
                               observed={}, actor="admin")
    _case("Injected instruction", "REFUSE_ISOLATE")
    _case("Tool outage", "HOLD_ESCALATE", "OPERATIONAL")
    a, b = _cases()
    for observed, message in (({a: "RETRY"}, "every case needs a result"),
                              ({a: "RETRY", b: "RETRY", "ST-99": "RETRY"}, "no such"),
                              ({a: "RETRY", b: "PANIC"}, "observed response must be")):
        with pytest.raises(DomainError, match=message):
            record_stress_test_run(ai_system_id="AIS-0001", occasion="Scheduled",
                                   observed=observed, actor="admin")
    with pytest.raises(DomainError, match="occasion must be one of"):
        record_stress_test_run(ai_system_id="AIS-0001", occasion="Whenever",
                               observed={a: "RETRY", b: "RETRY"}, actor="admin")


# --- Calibration ---------------------------------------------------------------------

def _pairs(agreeing, n=20):
    return [{"expert": 5, "judge": 5 if i < agreeing else 1} for i in range(n)]


def _calibrate(pairs, judge="AIS-JUDGE", **kw):
    return record_judge_calibration(**{"ai_system_id": "AIS-0001",
                                       "judge_ai_system_id": judge, "pairs": pairs,
                                       "dimension": "faithfulness", "actor": "admin",
                                       **kw})


def test_the_first_calibration_sets_the_level_and_a_drop_suspends_the_judge():
    _system()
    _system("AIS-JUDGE")
    _calibrate(_pairs(18))
    first = _data()["judge_calibrations"][0]
    assert first["is_baseline"] is True and first["agreement"] == 0.9
    _calibrate(_pairs(17))  # 0.85: exactly the tolerance, still inside
    _calibrate(_pairs(16))  # 0.80: outside
    rows = _data()["judge_calibrations"]
    assert [r["within_baseline"] for r in rows] == [True, True, False]
    assert rows[2]["baseline_level"] == 0.9 and rows[2]["is_baseline"] is False
    assert judge_reliance(rows) == {"AIS-JUDGE": "suspended"}
    _calibrate(_pairs(19))
    assert judge_reliance(_data()["judge_calibrations"]) == {"AIS-JUDGE": "in force"}
    assert "AIS-JUDGE" in judges_of(_data())


def test_adjacent_scores_count_as_agreement():
    _system()
    _system("AIS-JUDGE")
    _calibrate([{"expert": 4, "judge": 5}] * 20)
    assert _data()["judge_calibrations"][0]["agreement"] == 1.0


@pytest.mark.parametrize("kw, message", [
    ({"pairs": _pairs(10, n=19)}, "at least 20"),
    ({"pairs": [{"expert": 6, "judge": 5}] * 20}, "ACE scale"),
    ({"pairs": [{"expert": "4.5", "judge": 5}] * 20}, "ACE scale"),
    ({"pairs": _pairs(20), "dimension": "vibes"}, "dimension must be one of"),
    ({"pairs": _pairs(20), "judge": "AIS-0001"}, "its own judge"),
    ({"pairs": _pairs(20), "judge": "AIS-NOBODY"}, "not a registered AI System"),
    ({"pairs": _pairs(20), "judge": ""}, "judge_ai_system_id is required"),
])
def test_a_calibration_that_proves_nothing_is_refused(kw, message):
    _system()
    _system("AIS-JUDGE")
    with pytest.raises(DomainError, match=message):
        _calibrate(**kw)


def test_reliance_is_suspended_while_any_dimension_is_outside():
    rows = [{"judge_ai_system_id": "J", "dimension": "tone", "within_baseline": True},
            {"judge_ai_system_id": "J", "dimension": "safety", "within_baseline": False},
            {"judge_ai_system_id": "K", "dimension": "tone", "within_baseline": True}]
    assert judge_reliance(rows) == {"J": "suspended", "K": "in force"}


def test_evidence_cannot_be_recorded_on_a_hibernated_system():
    from src.governance.ai_system import retire_ai_system
    _system(ai_autonomy="SINGLE_CALL")
    retire_ai_system(ai_system_id="AIS-0001", actor="admin")
    with pytest.raises(DomainError, match="retired"):
        _trace()


def test_evidence_cannot_be_recorded_against_a_system_nobody_registered():
    with pytest.raises(DomainError, match="does not exist"):
        _trace(ai_system_id="AIS-NOBODY")
