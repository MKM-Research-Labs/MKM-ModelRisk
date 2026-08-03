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
"""Markdown content for the interim holding documents.

The prose templates the applier in ``scripts.file_holding_docs`` renders: the
monitoring-approach body and the remediation-evidence framework, each tailored
per model from its live record. Split out so the applier stays a small filing
pipeline (coding rule R2). Neither template fabricates a result or a piece of
evidence — both say so on their own status banner.
"""
from __future__ import annotations

# Which open findings map to which kind of remediation evidence. Keyed by the
# validation-question item_id; only the questions genuinely open on a given model
# produce a section, so each document lists that model's real outstanding items.
_EVIDENCE = {
    "VQ-002": ("Accuracy and stability",
        "Back-testing of the model's outputs against observed outcomes over a "
        "representative period, with error statistics and a stability check across "
        "re-runs and parameter perturbations."),
    "VQ-004": ("Override controls",
        "A documented, governed override procedure: the permitted overrides, who "
        "may authorise them, and a log showing each override with its "
        "justification and sign-off."),
    "VQ-005": ("Data quality",
        "Real observation records replacing the synthetic inputs, together with a "
        "data-quality assessment (completeness, accuracy, timeliness and source "
        "lineage) demonstrating the inputs are fit for purpose."),
    "VQ-008": ("Benchmarking",
        "A documented comparison against a named, credible independent "
        "alternative, with error metrics and a reconciliation explaining material "
        "differences."),
    "VQ-009": ("Independent validation",
        "A report from a reviewer independent of the model build who has "
        "replicated the results and issued a validation opinion, with any "
        "conditions or findings recorded."),
}

_OPEN = {"Not Addressed", "Partially Addressed"}


def _open_questions(data: dict) -> list[dict]:
    """The model's validation questions that are not fully Addressed."""
    return [q for q in (data.get("validation_questions") or [])
            if q.get("status") in _OPEN]


def build_monitoring_md(data: dict) -> str:
    """Markdown for the interim monitoring-approach holding document."""
    name = data.get("name", "")
    desc = data.get("description", "").strip()
    return f"""**Status: interim holding document.** This document sets out the
ongoing-monitoring approach for {name}. It has been produced ahead of the first
monitoring cycle, so it contains **no monitoring results** — only the design. It
is replaced by a monitoring result once the first cycle runs and produces dated
metrics.

# Scope

{desc}

# What is monitored

Monitoring tracks the model's material inputs and outputs and the limitation
triggers already recorded in its Limitations register. Where a sensitivity
analysis exists for the model, the quantities it identifies as most material are
the primary monitoring targets, because those are where drift moves the priced
result fastest.

# Metrics and thresholds

The following are tracked each cycle (thresholds are fixed at the first
calibration review and are not yet set):

- **Output stability** — drift in the model's headline output against the prior
  cycle and against the value at validation.
- **Input drift** — movement in the distribution of the model's key inputs
  relative to the calibration sample.
- **Exception rate** — the frequency of inputs falling outside the model's
  documented applicability range.

# Cadence

Periodic review (proposed: quarterly) plus an event-driven review triggered by a
material hazard event or a change in an upstream model this one depends on.

# Escalation and ownership

A threshold breach re-rates the model's RAG status and is escalated to the Model
Risk Committee, which decides whether recalibration, restriction or
re-validation is required. The model owner runs each cycle and records the
result.

# Exit from interim status

This holding document is superseded when the first monitoring cycle completes and
a dated monitoring result is filed in its place.
"""


def build_remediation_md(data: dict) -> str:
    """Markdown for the interim remediation-evidence framework holding document."""
    name = data.get("name", "")
    open_qs = _open_questions(data)
    if open_qs:
        lines = "\n".join(
            f"- **{q.get('short_label') or q.get('item_id')}** "
            f"({q.get('item_id')}) — currently {q.get('status')}."
            for q in open_qs)
    else:
        lines = "- No open validation questions are recorded for this model."

    sections = ""
    for q in open_qs:
        entry = _EVIDENCE.get(q.get("item_id"))
        if entry is None:
            continue
        heading, text = entry
        sections += f"\n## {heading} ({q.get('item_id')})\n\n{text}\n"
    if not sections:
        sections = ("\n## General\n\nEvidence appropriate to each open finding "
                    "as it is identified.\n")

    return f"""**Status: interim holding document.** This document describes the
*type* of evidence that would close each open finding on {name}. No remediation
evidence has yet been collected — it contains **no evidence**, only the standard
each item must meet. It is replaced, finding by finding, as real evidence is
produced.

# Open findings for this model

{lines}

# Appropriate evidence by finding
{sections}
# Acceptance criteria

To close a finding, the evidence must be dated, attributable to a named author,
reproducible from the inputs stated, and reviewed by someone independent of the
model build. Evidence that only restates the model's own construction does not
close a finding.
"""
