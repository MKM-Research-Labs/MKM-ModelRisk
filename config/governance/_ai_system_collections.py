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
"""The registers that hang off an AI System, apart from the record's own fields.

Split from ``_ai_system`` at the seam every record type has: a record's FIELDS say what
it is, and its COLLECTIONS are the registers kept against it — its tools, its
assumptions, its questions, what has been measured about it. They are edited by
different people at different moments and they grow at different rates; the field specs
barely move once a record type has settled, and the registers keep arriving.

Re-exported from ``_ai_system`` so every existing import goes on working.
"""
from __future__ import annotations

from config.governance._ai import AI_SYSTEM_QUESTION_LIST
from config.governance._assessments import MONITORING_COLLECTION
from config.governance._collections import (COLLECTION_SPECS, EVALUATIONS_COLLECTION,
                                            FAIRNESS_COLLECTION)
from config.governance._review import REVIEW_COLLECTION_SPECS
from config.governance._signoff_collections import SIGNOFF_COLLECTION_SPECS

AGENT_TOOLS_COLLECTION = "agent_tools"
AI_REVIEW_QUESTIONS_COLLECTION = "ai_review_questions"

AI_SYSTEM_COLLECTION_SPECS = {
    # Shared, unchanged, and named identically to a model's -- what the
    # ``identification`` and ``treatment`` probes read.
    "assumptions": COLLECTION_SPECS["assumptions"],
    "limitations": COLLECTION_SPECS["limitations"],
    "model_weaknesses": COLLECTION_SPECS["model_weaknesses"],
    "remediation_steps": COLLECTION_SPECS["remediation_steps"],
    "data_sources": COLLECTION_SPECS["data_sources"],
    # Same collection, same name, on all three record types: "who could this
    # disadvantage" is the same question of a model, an ML Application and an AI
    # System, and three shapes would make the estate-wide answer unobtainable.
    FAIRNESS_COLLECTION: COLLECTION_SPECS[FAIRNESS_COLLECTION],
    # What testing actually returned. Same collection on all three record types,
    # because "has this been measured, and what did it say" is one question.
    EVALUATIONS_COLLECTION: COLLECTION_SPECS[EVALUATIONS_COLLECTION],
    # The measured position on an output field, period by period. Same collection on
    # all three record types: "has this drifted, and did what it predicted happen" is
    # one question whatever produced the number, which is the whole reason the measures
    # library is shared.
    MONITORING_COLLECTION: COLLECTION_SPECS[MONITORING_COLLECTION],
    "change_history": COLLECTION_SPECS["change_history"],
    "operational_failure_events": COLLECTION_SPECS["operational_failure_events"],
    "actions": COLLECTION_SPECS["actions"],
    # One entry per tool or API the system may invoke. A collection rather than a
    # textarea because the agentic controls are asked tool by tool: AIR-PREV-018 is
    # about the authority of each one, and "what can this system reach" has to be a
    # query rather than a paragraph somebody has to read.
    AGENT_TOOLS_COLLECTION: {
        "label": "Tools and APIs", "id_prefix": "TOOL",
        "fields": [
            {"key": "name", "label": "Tool", "type": "textarea", "required": True},
            {"key": "purpose", "label": "What it is for", "type": "textarea"},
            {"key": "authority", "label": "What it may do", "type": "textarea"},
            {"key": "approval", "label": "Human approval required", "type": "choice",
             "options": ("Always", "Above a threshold", "Never")},
        ],
    },
    # Its own questionnaire, same shape as a model's validation questions, seeded
    # from its own admin list and held under its own name.
    AI_REVIEW_QUESTIONS_COLLECTION: COLLECTION_SPECS["validation_questions"],
    # Borrowed machinery, not reimplemented: the same challenge thread and sign-off
    # queue every other record uses, so an AI System takes the same trip through the
    # committee and evidences the same clauses.
    **REVIEW_COLLECTION_SPECS,
    **SIGNOFF_COLLECTION_SPECS,
}

__all__ = ["AGENT_TOOLS_COLLECTION", "AI_REVIEW_QUESTIONS_COLLECTION",
           "AI_SYSTEM_COLLECTION_SPECS"]
