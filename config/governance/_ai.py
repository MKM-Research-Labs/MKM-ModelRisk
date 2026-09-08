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
"""AI System vocabulary: foundation models and the AI questionnaire (rule R1).

The admin-managed lists an AI System picks from, kept apart from the record's own
field specs for the same reason ``_ml.py`` is kept apart from ``_ml_application.py``:
an institution curates these, and the record's shape is not theirs to change.

**Why this exists at all.** ``_ml.py`` says in its own words that LLMs and agentic
AI are out of scope and are not to be added to the estimator list. That still
holds -- an estimator is a fitted algorithm and a foundation model is not one, and
folding them into one list would leave "which version of GradientBoostingRegressor"
and "which snapshot of a vendor's frontier model" answering the same question. They
are different questions, so they are different lists and different records.

The FINOS AI Governance Framework is what changed. Its risk catalogue is entirely
about generative and agentic systems, and 19 of its 23 risk rows read Not evidenced
for one reason: no such system can be registered. See docs/design/finos-coverage.md
section 6.1.

**What this list is NOT.** It is no longer the whole questionnaire an AI System is
asked. Five questions — use case, human oversight, who could be disadvantaged,
explainability, and what would show it had stopped working — are asked of any
application of a model and live in ``_questions_common.py``; a record is copied those
first and these beneath them. What is left here is what is particular to a generative
or agentic system, which is the argument this module has always made and now makes
precisely: the PROCESSES stay separate, and the questions that are genuinely the same
question stop being asked twice in two wordings.

``FOUNDATION_MODEL_LIST`` seeds EMPTY, like the estimator list's versions do. Which
models an institution has approved is a fact about their procurement and their legal
review, and seeding our guesses would put models in their register that nobody has
cleared -- on a record type whose whole point is knowing what is actually running.
"""
from __future__ import annotations

from config.governance._ai_regimes import MARKETS_LIST

FOUNDATION_MODEL_LIST = "foundation_model"
AI_SYSTEM_QUESTION_LIST = "ai_system_questions"

# How the system is reached, which is the fact RC-001 turns on: what leaves the firm.
HOSTING_MODES = ("Third-party hosted API", "Private cloud deployment",
                 "On-premise", "Embedded in a vendor product")

# What the system is, architecturally. AIR-OP-014, AIR-OP-028 and the whole agentic
# half of the Security catalogue only bite on particular values here, which is why it
# is a field and not prose: "is anything in the estate agentic" has to be a query.
# The first five describe generative systems, which is what the register was built
# for. The sixth is here because not every governed AI system is one: a physics-informed
# or otherwise scientific model — a Bayesian estimator with a learned component, say —
# has an architecture the other five actively misdescribe, and asserting "Fine-tuned"
# of it would put a false fact on the record to satisfy a required field. It is a
# value the agentic controls do not match, which is the correct outcome rather than an
# omission: AGENTIC_PATTERNS is a membership test, so nothing keyed on it misfires.
DEPLOYMENT_PATTERNS = ("Direct prompting", "Retrieval-augmented (RAG)",
                       "Fine-tuned", "Agentic (tool-using)", "Multi-agent",
                       "Physics-informed / scientific ML")

# What the firm sends for inference. Ordered by how much it would matter if it
# leaked, so a reader can see at a glance which end of the list a record sits at.
DATA_EGRESS_CLASSES = ("No data leaves the firm", "Internal non-sensitive",
                       "Confidential business data", "Personal data (PII)",
                       "Regulated client data")

# Where the human is. AIR-OP-018 (overreach) and AIR-RC-022 (oversight) both turn on
# this, and it is the single most useful thing to know about an AI system in a bank.
HUMAN_OVERSIGHT_MODES = ("Human makes the decision", "Human reviews before action",
                         "Human reviews after the fact", "Human on request only",
                         "Fully autonomous")

# Whether the underlying model can change under the firm's feet (AIR-OP-005).
#
# "Not applicable" is last and is a real answer, not a way out of the question: a
# physics-informed or scientific ML system is not built on somebody's model, so there
# is no provider version to pin and no policy to state. Without it such a record is
# marked down for an absence that is not one, and a completeness score that reports
# unanswerable gaps is one people learn to ignore.
#
# It is NOT the answer for a system that does have a foundation model and has simply
# not decided — that is a blank, and the audit is right to ask about it.
VERSION_POLICIES = ("Pinned to a named version", "Pinned, reviewed on a cycle",
                    "Tracks the provider's latest", "Not applicable")

# EU AI Act Annex III risk classes. FINOS cites the Regulation directly (Articles 12,
# 26 and 72) and a deployer has to know which class it is in before it can know which
# obligations apply. "Not assessed" is the honest default and is not a class -- it is
# the absence of the assessment, which is itself the finding.
# The honest default, named so nothing has to compare against the literal: a probe
# that counted "Not assessed" as a classification would report the absence of the
# assessment as the assessment.
UNASSESSED_EU_CLASS = "Not assessed"
EU_AI_ACT_CLASSES = (UNASSESSED_EU_CLASS, "Minimal risk", "Limited risk",
                     "High risk (Annex III)", "Prohibited")

# The questionnaire seeded on a fresh install, and the reason this record type earns
# its own rather than borrowing the ML set: not one of the ten ML questions is
# answerable about a foundation model nobody in the firm trained. These are written
# against the FINOS risk catalogue, so that answering them is what moves those rows.
AI_SYSTEM_QUESTIONS = (
    {"short_label": "Model Provenance",
     "question": "Which foundation model and version is in use, who provides it, and "
                 "what happens when they change or retire it?"},
    {"short_label": "Data Egress",
     "question": "What data is sent for inference, does it leave the firm, and what "
                 "in the contract governs its retention and reuse?"},
    {"short_label": "Grounding and Accuracy",
     "question": "How is the output grounded, how has its accuracy been measured, and "
                 "against what reference answers?"},
    {"short_label": "Hallucination Exposure",
     "question": "What is the consequence of a confident but wrong answer reaching its "
                 "consumer, and what stops it?"},
    {"short_label": "Determinism",
     "question": "Can the same input produce different output, and does anything "
                 "downstream depend on it not doing so?"},
    {"short_label": "Prompt and Input Integrity",
     "question": "Could untrusted content reach the model as instructions, and what "
                 "filtering stands between the two?"},
    {"short_label": "Agency and Authority",
     "question": "What can this system do without a human, which tools or APIs can it "
                 "call, and what is the worst it could do if manipulated?"},
    {"short_label": "Regulatory Classification",
     "question": "Under the EU AI Act and any other applicable regime, what class does "
                 "this system fall into, and who decided that?"},
)

AI_REFERENCE_SPECS = {
    # Shaped like the Estimator list next door: one row per model a firm has approved,
    # carrying the versions it runs. NOT one row per version -- the same cartesian
    # product argument that keeps the estimator list readable.
    FOUNDATION_MODEL_LIST: {"label": "Foundation model", "id_prefix": "FM",
                            "display": "value", "fields": [
        {"key": "value", "label": "Foundation model", "type": "text", "required": True},
        {"key": "provider", "label": "Provider", "type": "text", "reference": "vendor"},
        {"key": "versions", "label": "Approved versions (comma-separated)", "type": "text"},
        {"key": "notes", "label": "Notes", "type": "textarea"},
    ]},
    AI_SYSTEM_QUESTION_LIST: {"label": "AI System questions", "id_prefix": "AIQ",
                              "display": "short_label", "fields": [
        {"key": "short_label", "label": "Topic", "type": "text", "required": True},
        {"key": "question", "label": "Question", "type": "textarea", "required": True},
    ]},
}

# Where systems are placed on the market or used. An admin list because which markets
# an institution serves is a fact about that institution, and a fixed list of ours would
# be wrong for a firm operating somewhere we did not think of.
MARKET_LIST_SPEC = {MARKETS_LIST: {"label": "Market", "id_prefix": "MK",
                                   "display": "value", "fields": [
    {"key": "value", "label": "Market", "type": "text", "required": True},
]}}
AI_REFERENCE_SPECS.update(MARKET_LIST_SPEC)

AI_REFERENCE_LISTS = (FOUNDATION_MODEL_LIST, AI_SYSTEM_QUESTION_LIST, MARKETS_LIST)

__all__ = ["UNASSESSED_EU_CLASS", "FOUNDATION_MODEL_LIST", "AI_SYSTEM_QUESTION_LIST", "AI_SYSTEM_QUESTIONS",
           "AI_REFERENCE_SPECS", "AI_REFERENCE_LISTS", "HOSTING_MODES",
           "DEPLOYMENT_PATTERNS", "DATA_EGRESS_CLASSES", "HUMAN_OVERSIGHT_MODES",
           "VERSION_POLICIES", "EU_AI_ACT_CLASSES"]
