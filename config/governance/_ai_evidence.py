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
"""The evidence an AI System's run produces: traces, stress tests, and judge calibration.

Three of the practice paper's nine concepts had nowhere to put their evidence until these
(spec v0.5 §9.1, §9.3; AIGov edition). Each is recorded as an immutable event, like a
configuration snapshot: evidence that could be edited afterwards would be a note about
what happened rather than a record of it.

**Traces (concept 2)** are held as hashed references, not stored (decided 2026-09-23): the
trace lives in the system's own observability stack and this platform records where it
is, its content hash, and which parts of the required content it holds. Required content
rises with autonomy and is cumulative — a workflow's trace owes everything a single
call's does, and more. ModelRisk holds the traces that are EVIDENCE (a benchmark run, a
sampled production run, an incident), not every run the system makes.

**Stress tests (concept 7)** are a register of cases on the record, each stating what the
system should do, and a run records what it did. The suite's version moves on its own
whenever the set of cases has changed since the last run, so a version number can never
be reused for a different suite.

**Calibration (concept 5)** reconciles expert grading with the judge's on the same items.
The first calibration sets the level; one that falls below it suspends reliance on that
judge's scores until a later calibration clears it.
"""
from __future__ import annotations

from config.governance._ai_complexity import (AI_AUTONOMY_AGENT, AI_AUTONOMY_SINGLE_CALL,
                                              AI_AUTONOMY_WORKFLOW)

# --- Traces ----------------------------------------------------------------------------

# What a trace must hold, by autonomy, each level adding to the one before. Keys are what
# a caller declares; labels are the practice paper's words.
_SINGLE = ("case_input", "model_snapshot", "controls_in_force", "output", "parser_result")
_WORKFLOW = _SINGLE + ("step_inputs_outputs", "retrieval_tool_responses",
                       "checks_retries_errors")
_AGENT = _WORKFLOW + ("step_graph", "tool_calls_state_changes", "chosen_path_context")
TRACE_REQUIRED_CONTENT: dict[str, tuple[str, ...]] = {
    AI_AUTONOMY_SINGLE_CALL: _SINGLE,
    AI_AUTONOMY_WORKFLOW: _WORKFLOW,
    AI_AUTONOMY_AGENT: _AGENT,
}
TRACE_CONTENT_LABELS = {
    "case_input": "Case input",
    "model_snapshot": "Model snapshot",
    "controls_in_force": "Controls in force",
    "output": "Output",
    "parser_result": "Parser result",
    "step_inputs_outputs": "Each step's inputs and outputs",
    "retrieval_tool_responses": "Retrieval and tool responses",
    "checks_retries_errors": "Checks, retries and errors",
    "step_graph": "Typed step graph",
    "tool_calls_state_changes": "Tool calls and the state changes they caused",
    "chosen_path_context": "Path chosen, with the context at each branch",
}
# Why this run's trace is being kept. What makes it evidence rather than a log line.
TRACE_PURPOSES = ("Benchmark run", "Envelope run", "Production sample", "Stress test",
                  "Incident")
# SHA-256, as hex. The algorithm is named so a reader can recompute it.
TRACE_HASH_ALGORITHM = "sha256"
TRACE_HASH_HEX_LENGTH = 64

# --- Stress tests ----------------------------------------------------------------------

STRESS_CASES_COLLECTION = "stress_test_cases"
STRESS_CATEGORIES = ("ADVERSARIAL", "OPERATIONAL")
STRESS_CATEGORY_LABELS = {
    "ADVERSARIAL": "Adversarial — prompt injection, poisoned retrieval",
    "OPERATIONAL": "Operational — timeout, rate limit, tool or data outage",
}
STRESS_RESPONSES = ("REFUSE_ISOLATE", "RETRY", "HOLD_ESCALATE")
STRESS_RESPONSE_LABELS = {
    "REFUSE_ISOLATE": "Refuse or isolate",
    "RETRY": "Retry within budget",
    "HOLD_ESCALATE": "Hold and escalate",
}
# When a suite is run. The paper asks for before release and after every Material change.
STRESS_OCCASIONS = ("Before release", "After a Material change", "Scheduled")

STRESS_CASES_SPEC = {
    STRESS_CASES_COLLECTION: {"label": "Stress-test cases", "id_prefix": "ST", "fields": [
        {"key": "scenario", "label": "What is thrown at it", "type": "textarea",
         "required": True},
        {"key": "category", "label": "Category", "type": "choice",
         "options": STRESS_CATEGORIES, "option_labels": STRESS_CATEGORY_LABELS,
         "required": True},
        {"key": "expected_response", "label": "What it should do", "type": "choice",
         "options": STRESS_RESPONSES, "option_labels": STRESS_RESPONSE_LABELS,
         "required": True},
        # The failure-mode register entries this case exercises, by id (FM-...). Free
        # text, like the FINOS pair on a failure mode, so a case can name several.
        {"key": "failure_modes", "label": "Failure modes exercised (FM-…)", "type": "text"},
    ]},
}

# --- Calibration (Anchored Continuous Evaluation) --------------------------------------

# An expert and the judge agree on an item when their scores on the ACE scale are at most
# this far apart. 0 is exact agreement; 1 is "adjacent", the usual reading on a five-point
# anchored scale, where one point is the width of an honest disagreement.
CALIBRATION_AGREEMENT_WITHIN = 1
# How far agreement may fall below the baseline level before reliance is suspended.
CALIBRATION_TOLERANCE = 0.05
JUDGE_RELIANCE_IN_FORCE = "in force"
JUDGE_RELIANCE_SUSPENDED = "suspended"
JUDGE_RELIANCE_UNCALIBRATED = "not calibrated"

# --- Trajectory scores (concept 6) -------------------------------------------------------

# Scored against a recorded trace, never on its own: the trace is the evidence and the
# score reads from it. Where a reference trajectory exists, the run is compared with it by
# graph-edit distance (MKM's measure, not the paper's); this is the similarity below which
# the path is not acceptable, whatever it returned. Where none exists, the assessor judges
# the run against stated criteria and must say what they were.
TRAJECTORY_MIN_SIMILARITY = 0.8


__all__ = ["CALIBRATION_AGREEMENT_WITHIN", "CALIBRATION_TOLERANCE",
           "JUDGE_RELIANCE_IN_FORCE", "JUDGE_RELIANCE_SUSPENDED",
           "JUDGE_RELIANCE_UNCALIBRATED", "STRESS_CASES_COLLECTION", "STRESS_CASES_SPEC",
           "STRESS_CATEGORIES", "STRESS_CATEGORY_LABELS", "STRESS_OCCASIONS",
           "STRESS_RESPONSES", "STRESS_RESPONSE_LABELS", "TRACE_CONTENT_LABELS",
           "TRACE_HASH_ALGORITHM", "TRACE_HASH_HEX_LENGTH", "TRACE_PURPOSES",
           "TRACE_REQUIRED_CONTENT", "TRAJECTORY_MIN_SIMILARITY"]
