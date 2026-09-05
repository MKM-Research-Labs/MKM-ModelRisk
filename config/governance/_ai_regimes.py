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
"""Regulatory regimes as data: which apply to a system, and what each asks of it.

A framework in ``_frameworks.py`` applies to the whole estate — ISO 31000 is either the
firm's reference or it is not. A REGIME does not. The EU AI Act binds a system placed on
the Union market and says nothing about one that never leaves a US desk, so a regime
carries the conditions under which it bites, and every regime here is answered per
record rather than per institution.

**Applicability is derived from the record, never ticked.** "Which regimes apply to this
system" is a question with a right answer given where it is used and what it does, and a
checkbox somebody ticks is an assertion nobody can check. It is derived from the fields
the record already carries, and the derivation states its reason so a compliance officer
can disagree with it on the facts rather than on the conclusion.

**No compliance claim, as everywhere else in this platform.** These rows say what the
platform holds against each obligation and which systems it applies to. Whether the firm
complies is the firm's assessment; several clauses are marked as evidenced outside any
tool because they are about people and process rather than records.

The clause references follow each instrument's published structure. An adopter citing
them in a document a supervisor reads should check them against their own copy: the
MAPPING is the judgement offered here, the numbering is not.
"""
from __future__ import annotations

from typing import Any

# --- Where a system is used --------------------------------------------------
# The fact regime applicability turns on and the record did not carry. Deliberately
# "placed on the market or used in", which is the Act's own test and is broader than
# where the firm is domiciled: a London desk serving EU customers is in scope, and a
# field asking where the TEAM sits would have said otherwise.
MARKETS_FIELD = "markets"
MARKETS_LIST = "market"
DEFAULT_MARKETS = ("European Union", "United Kingdom", "United States",
                   "Rest of world")

# --- The regimes -------------------------------------------------------------
# ``applies_when`` is read the way the routing rules are: every named field must hold
# one of the listed values. A regime with no conditions applies to every AI System.
#
# ``markets`` is multi-valued on the record, so a match means an intersection — a
# system serving the EU and the US is in scope of the Act for its EU use, which is how
# the Act works and is why this is not an equality test.
EU_AI_ACT = "EU AI Act (Regulation 2024/1689)"
PRA_SS1_23 = "PRA SS1/23 — Model risk management principles"
NIST_AI_600_1 = "NIST AI 600-1 — Generative AI Profile"

AI_REGIMES: tuple[dict[str, Any], ...] = (
    {
        "name": EU_AI_ACT,
        "applies_when": {MARKETS_FIELD: ("European Union",)},
        "because": "Placed on the market or used in the European Union.",
        "clauses": (
            ("Art. 6", "Classification as high-risk", "ai_regulatory_class",
             "The record's own EU AI Act class, and the rationale beside it. An "
             "unclassified system is the finding here — 'Not assessed' is the absence "
             "of the assessment, not a class."),
            ("Art. 9", "Risk management system", "identification",
             "The assumptions, limitations and weaknesses recorded against the system, "
             "which is the risk register the Article asks to be maintained across the "
             "lifecycle."),
            ("Art. 12", "Record-keeping and logging", "inventory",
             "The record exists and its history is append-only. What the platform does "
             "NOT hold is the system's own runtime logs, which is what Art. 12 is "
             "mostly about — this evidences the governance record, not the event log."),
            ("Art. 13", "Transparency and provision of information", "ai_explainability",
             "How an output is explained to the person affected by it."),
            ("Art. 14", "Human oversight", "ai_oversight",
             "Who reviews what it produces and on what basis, recorded as a stated "
             "oversight mode rather than a claim that a human is involved."),
            ("Art. 15", "Accuracy, robustness and cybersecurity", "acceptance",
             "Unit, integration and benchmark testing recorded against the system. "
             "Robustness against adversarial input is evidenced by a red-team "
             "evaluation where one has been run."),
            ("Art. 17", "Quality management system", "institution",
             "A management system is a fact about how the firm runs, not a record this "
             "platform holds."),
            ("Art. 26", "Obligations of deployers", "accountability",
             "A named owner accountable for the system's use."),
            ("Art. 72", "Post-market monitoring", "monitoring",
             "Whether the system's monitoring is in date."),
        ),
    },
    {
        "name": PRA_SS1_23,
        "applies_when": {MARKETS_FIELD: ("United Kingdom",)},
        "because": "Used in the United Kingdom, where SS1/23 applies to firms in scope "
                   "of the PRA's model risk expectations.",
        "clauses": (
            ("1", "Model identification and model risk classification", "analysis",
             "Tier, materiality and complexity with their rationales — the "
             "classification Principle 1 asks to be applied consistently."),
            ("2", "Governance", "committee",
             "The committee that signed the system off."),
            ("3", "Model development, implementation and use", "identification",
             "What the system assumes and where it may not be used."),
            ("4", "Independent model validation", "independence",
             "A reviewer other than the owner, measured on the record rather than "
             "asserted in a policy."),
            ("5", "Model risk mitigants", "treatment",
             "Remediation recorded where the rating calls for it."),
        ),
    },
    {
        "name": NIST_AI_600_1,
        # No market condition: the Profile is voluntary guidance a firm adopts, and it
        # is written for generative systems specifically — so it applies wherever the
        # deployment pattern says the system is one.
        "applies_when": {},
        "because": "Voluntary guidance the firm has adopted for generative systems.",
        "clauses": (
            ("2.2", "Confabulation", "ai_grounding",
             "How the output is grounded, and who would catch it being wrong."),
            ("2.6", "Harmful bias and homogenization", "fairness",
             "A recorded fairness assessment naming what was measured and what it "
             "showed."),
            ("2.7", "Human-AI configuration", "ai_oversight",
             "The stated oversight mode."),
            ("2.9", "Information security", "ai_egress",
             "What leaves the firm for inference and what in the contract permits it."),
            ("2.12", "Value chain and component integration", "ai_provider",
             "The foundation model and provider named on the record, and the version "
             "policy that governs how it changes underneath."),
        ),
    },
)


def matches(regime: dict[str, Any], data: dict[str, Any]) -> bool:
    """Whether a regime's conditions hold for a record.

    A multi-valued field on the record matches if ANY of its values is listed — a
    system serving the EU and the US is in scope of the Act for its EU use.
    """
    for field, allowed in (regime.get("applies_when") or {}).items():
        held = data.get(field)
        values = held if isinstance(held, (list, tuple, set)) else [held]
        if not any(str(v or "") in allowed for v in values):
            return False
    return True


def regimes_for(data: dict[str, Any]) -> list[dict[str, Any]]:
    """The regimes that apply to one record, each with the reason it does."""
    return [{"name": r["name"], "because": r["because"], "clauses": len(r["clauses"])}
            for r in AI_REGIMES if matches(r, data)]


# Shaped exactly like FRAMEWORK_COVERAGE so the 0.5 mapping engine reports these
# without knowing they are regimes rather than frameworks.
REGIME_COVERAGE = tuple((r["name"], r["clauses"]) for r in AI_REGIMES)

REGIME_NOTES = {
    r["name"]: (r["because"] + " These rows state what the platform holds against each "
                "obligation; whether the firm complies is the firm's own assessment.")
    for r in AI_REGIMES
}

__all__ = ["AI_REGIMES", "DEFAULT_MARKETS", "EU_AI_ACT", "MARKETS_FIELD",
           "MARKETS_LIST", "NIST_AI_600_1", "PRA_SS1_23", "REGIME_COVERAGE",
           "REGIME_NOTES", "matches", "regimes_for"]
