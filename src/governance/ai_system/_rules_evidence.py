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
"""Run-evidence decisions for an AI System: trace references, stress-test runs, and judge
calibration (config/governance/_ai_evidence.py says what each is and why).

Pure, like the other rules modules: no I/O, and every refusal is a DomainError with the
reason in it. The command layer does what needs a read — that the judge exists.

What is COMPUTED here is computed from what the caller sent, never taken from it: whether
a trace is complete, whether a stress case passed, what agreement a calibration showed.
A caller that posted its own verdict would have answered the question the record exists
to ask.
"""
from __future__ import annotations

import hashlib
import json
import string
from typing import Any

from config.governance._ai_ace import ACE_DIMENSIONS, ACE_MIN_SAMPLES, ACE_SCALE
from config.governance._ai_evidence import (CALIBRATION_AGREEMENT_WITHIN,
                                            CALIBRATION_TOLERANCE,
                                            JUDGE_RELIANCE_IN_FORCE,
                                            JUDGE_RELIANCE_SUSPENDED,
                                            JUDGE_RELIANCE_UNCALIBRATED,
                                            STRESS_CASES_COLLECTION, STRESS_OCCASIONS,
                                            STRESS_RESPONSES, TRACE_CONTENT_LABELS,
                                            TRACE_HASH_HEX_LENGTH, TRACE_PURPOSES,
                                            TRACE_REQUIRED_CONTENT)
from src.governance.ai_system._state import (EVENT_CALIBRATION_RECORDED,
                                             EVENT_STRESS_RUN_RECORDED,
                                             EVENT_TRACE_RECORDED, AISystemState)
from src.governance.errors import DomainError


def _require_editable(state: AISystemState) -> None:
    # Repeated rather than imported, for the reason _rules_baseline gives.
    if not state.exists:
        raise DomainError("AI System does not exist")
    if state.retired:
        raise DomainError("AI System is retired")


def _config_version(state: AISystemState) -> int:
    """The configuration in force. Evidence that cannot say what it ran under would
    outlive any change to it silently — the envelope refuses for the same reason."""
    if not state.snapshots:
        raise DomainError("take a configuration snapshot first: evidence has to say "
                          "which configuration it was produced under")
    return len(state.snapshots)


# --- Traces ---------------------------------------------------------------------------

def decide_record_trace(
    state: AISystemState, *, run_id: str, trace_uri: str, content_hash: str,
    contents, purpose: str, recorded_at: str,
) -> tuple[str, dict[str, Any]]:
    """Record a reference to one run's trace, and how complete it is.

    An incomplete trace is RECORDED, not refused, with what it is missing: a trace that
    cannot walk back from output to cause is itself the finding, and refusing it would
    leave the gap with no record at all.
    """
    _require_editable(state)
    autonomy = state.fields.get("ai_autonomy")
    if autonomy not in TRACE_REQUIRED_CONTENT:
        raise DomainError("set the system's autonomy first: what a trace must hold "
                          "depends on it")
    run_id, trace_uri = str(run_id or "").strip(), str(trace_uri or "").strip()
    if not run_id or not trace_uri:
        raise DomainError("run_id and trace_uri are required")
    if any(t.get("run_id") == run_id for t in state.traces):
        raise DomainError(f"a trace for run {run_id} is already recorded")
    digest = str(content_hash or "").strip().lower()
    if len(digest) != TRACE_HASH_HEX_LENGTH or set(digest) - set(string.hexdigits.lower()):
        raise DomainError("content_hash must be a SHA-256 digest in hex")
    if purpose not in TRACE_PURPOSES:
        raise DomainError(f"purpose must be one of: {', '.join(TRACE_PURPOSES)}")
    held = [str(c) for c in (contents or [])]
    unknown = sorted(set(held) - set(TRACE_CONTENT_LABELS))
    if unknown:
        raise DomainError(f"unknown trace content: {', '.join(unknown)}")
    missing = [c for c in TRACE_REQUIRED_CONTENT[autonomy] if c not in held]
    return EVENT_TRACE_RECORDED, {
        "run_id": run_id, "config_version": _config_version(state), "autonomy": autonomy,
        "trace_uri": trace_uri, "content_hash": digest, "contents": sorted(set(held)),
        "missing": missing, "complete": not missing, "purpose": purpose,
        "recorded_at": recorded_at,
    }


# --- Stress tests ---------------------------------------------------------------------

def _suite_digest(cases: list[dict[str, Any]]) -> str:
    return hashlib.sha256(json.dumps(cases, sort_keys=True).encode()).hexdigest()


def decide_record_stress_run(
    state: AISystemState, *, occasion: str, observed: dict[str, Any], run_at: str,
) -> tuple[str, dict[str, Any]]:
    """Record one run of the whole suite: what each case did against what it should have.

    The run copies the cases it was judged against, so a later edit to the register does
    not rewrite what an earlier run passed. Every case must have a result — a run that
    skipped the awkward ones is not a run of the suite.
    """
    _require_editable(state)
    if occasion not in STRESS_OCCASIONS:
        raise DomainError(f"occasion must be one of: {', '.join(STRESS_OCCASIONS)}")
    register = state.collections.get(STRESS_CASES_COLLECTION) or ()
    if not register:
        raise DomainError("the stress-test suite has no cases yet")
    observed = dict(observed or {})
    ids = [c["item_id"] for c in register]
    unknown = sorted(set(observed) - set(ids))
    if unknown:
        raise DomainError(f"no such stress-test case: {', '.join(unknown)}")
    unrun = [i for i in ids if not observed.get(i)]
    if unrun:
        raise DomainError(f"every case needs a result; none for {', '.join(unrun)}")
    bad = sorted(v for v in observed.values() if v not in STRESS_RESPONSES)
    if bad:
        raise DomainError(f"observed response must be one of: {', '.join(STRESS_RESPONSES)}")
    cases = [{"case_id": c["item_id"], "scenario": c.get("scenario"),
              "category": c.get("category"), "expected_response": c.get("expected_response"),
              "failure_modes": c.get("failure_modes") or ""} for c in register]
    digest = _suite_digest(cases)
    last = state.stress_runs[-1] if state.stress_runs else None
    version = (last["suite_version"] if last and last["suite_digest"] == digest
               else (last["suite_version"] + 1 if last else 1))
    for case in cases:
        case["observed_response"] = observed[case["case_id"]]
        case["passed"] = case["observed_response"] == case["expected_response"]
    return EVENT_STRESS_RUN_RECORDED, {
        "suite_version": version, "suite_digest": digest,
        "config_version": _config_version(state), "occasion": occasion, "cases": cases,
        "failed": [c["case_id"] for c in cases if not c["passed"]],
        "passed": all(c["passed"] for c in cases), "run_at": run_at,
    }


# --- Calibration ----------------------------------------------------------------------

def _score(value: Any) -> int:
    try:
        score = int(value)
    except (TypeError, ValueError):
        score = None
    if score not in ACE_SCALE or str(value).strip() != str(score):
        raise DomainError(f"scores must be on the ACE scale {min(ACE_SCALE)}–{max(ACE_SCALE)}")
    return score


def decide_record_calibration(
    state: AISystemState, *, ai_system_id: str, judge_ai_system_id: str, pairs,
    dimension: str, recorded_at: str,
) -> tuple[str, dict[str, Any]]:
    """Reconcile expert and judge scores on the same items, and say whether the judge
    still agrees as well as it did at baseline.

    The first calibration for a judge on a dimension IS the baseline. After that, one
    whose agreement falls more than ``CALIBRATION_TOLERANCE`` below it is outside the
    level, and reliance on the judge's scores is suspended until one comes back inside.
    """
    _require_editable(state)
    judge = str(judge_ai_system_id or "").strip()
    if not judge:
        raise DomainError("judge_ai_system_id is required")
    if judge == ai_system_id:
        raise DomainError("a system cannot be its own judge")
    if dimension not in ACE_DIMENSIONS:
        raise DomainError(f"dimension must be one of: {', '.join(ACE_DIMENSIONS)}")
    scored = [(_score(p.get("expert")), _score(p.get("judge"))) for p in (pairs or [])]
    if len(scored) < ACE_MIN_SAMPLES:
        raise DomainError(f"at least {ACE_MIN_SAMPLES} expert-graded items are needed; "
                          f"{len(scored)} given")
    agreed = sum(1 for e, j in scored if abs(e - j) <= CALIBRATION_AGREEMENT_WITHIN)
    agreement = round(agreed / len(scored), 4)
    baseline = next((c for c in state.calibrations if c["judge_ai_system_id"] == judge
                     and c["dimension"] == dimension and c["is_baseline"]), None)
    level = baseline["agreement"] if baseline else agreement
    return EVENT_CALIBRATION_RECORDED, {
        "judge_ai_system_id": judge, "dimension": dimension, "sample_size": len(scored),
        "pairs": [{"expert": e, "judge": j} for e, j in scored],
        "agreement": agreement, "is_baseline": baseline is None, "baseline_level": level,
        "within_baseline": agreement >= level - CALIBRATION_TOLERANCE,
        "recorded_at": recorded_at,
    }


def judge_reliance(calibrations) -> dict[str, str]:
    """``{judge: status}`` from the latest calibration of each judge on each dimension.

    A judge is suspended while ANY dimension's latest calibration is outside its level:
    a judge trusted on tone and not on faithfulness is not one whose scores can be
    relied on unread.
    """
    latest: dict[tuple[str, str], dict] = {}
    for c in calibrations or []:
        latest[(c["judge_ai_system_id"], c["dimension"])] = c
    status: dict[str, str] = {}
    for (judge, _), c in latest.items():
        if not c["within_baseline"]:
            status[judge] = JUDGE_RELIANCE_SUSPENDED
        else:
            status.setdefault(judge, JUDGE_RELIANCE_IN_FORCE)
    return status


__all__ = ["JUDGE_RELIANCE_UNCALIBRATED", "decide_record_calibration",
           "decide_record_stress_run", "decide_record_trace", "judge_reliance"]
