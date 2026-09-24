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
"""Scoring an agent's trajectory: the path it took, not only what it returned.

Concept 6 of the practice paper (spec v0.5 §9.3, AIGov edition). An agent can reach a
plausible answer through an unsupported step or a missed cross-check, and a check on the
answer alone cannot tell that run from a sound one. So the captured path is scored at
three levels — each material step, each connected sequence, the run as a whole — and the
run is ACCEPTABLE only if all three are: a clean final path does not excuse a step that
was not supported.

Scored against a recorded trace and only against one. The trace is the single evidence
source (§9.1); a score with no trace behind it would be a claim about a run nobody can
walk back through. Pure, like the other rules modules.
"""
from __future__ import annotations

from typing import Any

from config.governance._ai_complexity import AI_AUTONOMY_AGENT
from config.governance._ai_evidence import TRAJECTORY_MIN_SIMILARITY
from src.governance.ai_system._state import EVENT_TRAJECTORY_SCORED, AISystemState
from src.governance.ai_system.trajectory import edit_distance
from src.governance.errors import DomainError


def _levels(rows, name: str, checks: tuple[str, str]) -> dict[str, bool]:
    """``{label: passed}`` for one level, each row passing only when both checks do."""
    scored: dict[str, bool] = {}
    for row in rows or []:
        label = str((row or {}).get(name) or "").strip()
        if not label:
            raise DomainError(f"every {name} needs a name")
        if label in scored:
            raise DomainError(f"{name} {label} is scored twice")
        values = [(row or {}).get(c) for c in checks]
        if any(not isinstance(v, bool) for v in values):
            raise DomainError(f"{name} {label} needs {checks[0]} and {checks[1]} as "
                              "true or false")
        scored[label] = all(values)
    if not scored:
        raise DomainError(f"at least one {name} must be scored")
    return scored


def decide_score_trajectory(
    state: AISystemState, *, run_id: str, steps, sequences, observed_path=None,
    reference_trajectory_id: str = "", reference_path=None, run_acceptable=None,
    criteria: str = "", scored_at: str,
) -> tuple[str, dict[str, Any]]:
    """Score one recorded agent run at step, sequence and run level."""
    if not state.exists:
        raise DomainError("AI System does not exist")
    if state.retired:
        raise DomainError("AI System is retired")
    trace = next((t for t in state.traces if t.get("run_id") == run_id), None)
    if trace is None:
        raise DomainError(f"no trace is recorded for run {run_id}: a trajectory is "
                          "scored from its trace")
    if trace.get("autonomy") != AI_AUTONOMY_AGENT:
        raise DomainError("trajectories are scored for agent runs only")
    if any(s.get("run_id") == run_id for s in state.trajectory_scores):
        raise DomainError(f"run {run_id} is already scored")
    step_scores = _levels(steps, "step", ("supported", "permissible"))
    sequence_scores = _levels(sequences, "sequence", ("coherent", "complete"))
    reference = str(reference_trajectory_id or "").strip()
    if reference:
        observed, expected = list(observed_path or []), list(reference_path or [])
        if not observed or not expected:
            raise DomainError("a reference trajectory needs both the observed and the "
                              "reference path")
        distance = edit_distance(observed, expected)
        run_score = round(1 - distance / max(len(observed), len(expected)), 4)
        run_ok, method = run_score >= TRAJECTORY_MIN_SIMILARITY, "graph-edit distance"
    else:
        if not isinstance(run_acceptable, bool) or not str(criteria or "").strip():
            raise DomainError("without a reference trajectory, the run is judged "
                              "against stated criteria: give both the criteria and "
                              "whether the run met them")
        distance, run_score, run_ok, method = None, None, run_acceptable, "criteria"
    return EVENT_TRAJECTORY_SCORED, {
        "run_id": run_id, "config_version": trace.get("config_version"),
        "step_scores": step_scores, "sequence_scores": sequence_scores,
        "reference_trajectory_id": reference or None, "method": method,
        "edit_distance": distance, "run_score": run_score,
        "criteria": str(criteria or "").strip() or None, "run_acceptable": run_ok,
        "acceptable": run_ok and all(step_scores.values())
        and all(sequence_scores.values()),
        "failed_steps": [k for k, v in step_scores.items() if not v],
        "failed_sequences": [k for k, v in sequence_scores.items() if not v],
        "scored_at": scored_at,
    }


__all__ = ["decide_score_trajectory"]
