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
"""Scoring an agent's trajectory (concept 6; spec v0.5 §9.3, AIGov edition).

A trajectory is scored from a recorded agent trace, at step, sequence and run level, and
the run is acceptable only when all three are — a clean path does not excuse a step that
was not supported.
"""
from __future__ import annotations

import pytest

from src.governance.ai_system import (get_ai_system, rebuild_ai_system_view,
                                      record_run_trace, register_ai_system,
                                      retire_ai_system, score_trajectory,
                                      take_configuration_snapshot,
                                      update_ai_system_field)
from src.governance.errors import DomainError

_MIN = {"name": "Credit memo agent", "division": "Risk", "owner": "David K Kelly",
        "use_case": "Assembles a credit memo from the obligor file.",
        "deployment_pattern": "Agentic (tool-using)", "ai_autonomy": "AGENT"}
_STEPS = [{"step": "retrieve", "supported": True, "permissible": True},
          {"step": "extract", "supported": True, "permissible": True}]
_SEQS = [{"sequence": "retrieve→extract→reason", "coherent": True, "complete": True}]
_PATH = ["retrieve", "extract", "cross-check", "reason", "result"]


def _agent(run_id="R1", **fields):
    register_ai_system(ai_system_id="AIS-0001", fields={**_MIN, **fields}, actor="admin")
    take_configuration_snapshot(ai_system_id="AIS-0001", actor="admin")
    record_run_trace(ai_system_id="AIS-0001", run_id=run_id, trace_uri="otel://R1",
                     content_hash="ab" * 32, contents=[], purpose="Production sample",
                     actor="admin")


def _score(**kw):
    args = {"ai_system_id": "AIS-0001", "run_id": "R1", "steps": _STEPS,
            "sequences": _SEQS, "reference_trajectory_id": "REF-1",
            "observed_path": _PATH, "reference_path": _PATH, "actor": "admin", **kw}
    score_trajectory(**args)
    rebuild_ai_system_view()
    return get_ai_system("AIS-0001")["data"]["trajectory_scores"][-1]


def test_a_path_matching_its_reference_is_acceptable():
    _agent()
    s = _score()
    assert s["method"] == "graph-edit distance" and s["edit_distance"] == 0
    assert s["run_score"] == 1.0 and s["acceptable"] is True and s["config_version"] == 1


def test_a_missed_cross_check_costs_the_run_its_similarity():
    """The paper's own example: the cross-check is skipped. One deletion in five is
    0.8 — exactly the bar, so it still passes; skipping two does not."""
    _agent()
    assert _score(observed_path=["retrieve", "extract", "reason", "result"])[
        "run_score"] == 0.8
    s = _agent_second_run(observed_path=["retrieve", "extract", "result"])
    assert s["run_score"] == 0.6 and s["run_acceptable"] is False
    assert s["acceptable"] is False


def _agent_second_run(**kw):
    record_run_trace(ai_system_id="AIS-0001", run_id="R2", trace_uri="otel://R2",
                     content_hash="cd" * 32, contents=[], purpose="Incident",
                     actor="admin")
    return _score(run_id="R2", **kw)


def test_a_clean_path_does_not_excuse_an_unsupported_step():
    _agent()
    s = _score(steps=[*_STEPS, {"step": "reason", "supported": False,
                                "permissible": True}])
    assert s["run_acceptable"] is True and s["acceptable"] is False
    assert s["failed_steps"] == ["reason"]


def test_an_incomplete_sequence_fails_the_run_too():
    _agent()
    s = _score(sequences=[{"sequence": "extract→reason", "coherent": True,
                           "complete": False}])
    assert s["acceptable"] is False and s["failed_sequences"] == ["extract→reason"]


def test_without_a_reference_the_run_is_judged_against_stated_criteria():
    _agent()
    s = _score(reference_trajectory_id="", run_acceptable=True,
               criteria="Every figure traced to the obligor file; no external calls.")
    assert s["method"] == "criteria" and s["run_score"] is None
    assert s["acceptable"] is True and s["criteria"].startswith("Every figure")


@pytest.mark.parametrize("kw, message", [
    ({"run_id": "R9"}, "no trace is recorded for run R9"),
    ({"steps": []}, "at least one step"),
    ({"steps": [{"step": "", "supported": True, "permissible": True}]}, "needs a name"),
    ({"steps": [_STEPS[0], _STEPS[0]]}, "scored twice"),
    ({"steps": [{"step": "x", "supported": "yes", "permissible": True}]},
     "true or false"),
    ({"sequences": []}, "at least one sequence"),
    ({"reference_path": []}, "both the observed and the reference path"),
    ({"reference_trajectory_id": "", "run_acceptable": True}, "stated criteria"),
    ({"reference_trajectory_id": "", "criteria": "x"}, "stated criteria"),
])
def test_a_score_that_proves_nothing_is_refused(kw, message):
    _agent()
    with pytest.raises(DomainError, match=message):
        _score(**kw)


def test_a_run_is_scored_once():
    _agent()
    _score()
    with pytest.raises(DomainError, match="already scored"):
        _score()


def test_only_agent_runs_have_trajectories():
    _agent(ai_autonomy="WORKFLOW")
    with pytest.raises(DomainError, match="agent runs only"):
        _score()


def test_the_trace_decides_not_the_record_today():
    """A run traced as an agent stays an agent run if the record is reclassified."""
    _agent()
    update_ai_system_field(ai_system_id="AIS-0001", field="ai_autonomy",
                           value="WORKFLOW", actor="admin")
    assert _score()["acceptable"] is True


def test_scoring_needs_a_live_registered_system():
    with pytest.raises(DomainError, match="does not exist"):
        _score()
    _agent()
    retire_ai_system(ai_system_id="AIS-0001", actor="admin")
    with pytest.raises(DomainError, match="retired"):
        _score()
