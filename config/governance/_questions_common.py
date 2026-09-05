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
"""The questions asked of any application of a model, authored once.

An ML Application and an AI System are governed by two deliberately separate processes,
and the questions that make them different — training data and leakage on one side,
grounding and agency on the other — belong to those processes and stay there. But five
questions are asked of BOTH, because they are questions about using a model to affect
somebody rather than about how the model works. Those are here.

**Why this is not just tidiness.** The two lists had "Use Case" and "Explainability"
worded differently — "what decision does this model inform" against "what decision or
task does this system support" — which reads as a distinction and is not one. Two
populations answering differently-worded versions of one question cannot be reported
together, and a coverage question like "which records have said who could be
disadvantaged" has to be asked twice and reconciled by hand.

Three of the five were on one list and not the other, which was the real finding.
Only AI Systems were asked who could be disadvantaged, though a model that ranks retail
applicants raises that exactly as a generative system does — the fairness probe already
counts over the whole estate for the same reason. Only ML Applications were asked what
would show it had stopped working. Neither omission was deliberate.

**A record keeps the questionnaire it was registered with.** These are copied onto a
record at registration and never rewritten, so an estate seeded before this list existed
goes on answering the wording it was actually asked. That is correct — a review answers
the question that was put to it — and it is why this had to land before the questionnaire
was ever seeded rather than after.
"""
from __future__ import annotations

COMMON_QUESTION_LIST = "common_questions"

# Asked first, before either type's own. The order is part of the contract (see
# ``compose_questions``): a reviewer opening any record meets the same five questions in
# the same order, whatever kind of thing it is.
COMMON_QUESTIONS = (
    {"short_label": "Use Case",
     "question": "What decision or task does this support, and what is it explicitly "
                 "not to be used for?"},
    {"short_label": "Human Oversight",
     "question": "Who reviews what it produces, on what basis, and would they catch it "
                 "being wrong?"},
    {"short_label": "Bias and Fairness",
     "question": "Who could be disadvantaged by its output, and how would you know?"},
    {"short_label": "Explainability",
     "question": "Can a particular output be explained to the person affected by it, "
                 "and to a regulator?"},
    {"short_label": "Drift and Monitoring",
     "question": "What would show that it has stopped working, and who is watching "
                 "for it?"},
)

COMMON_REFERENCE_SPECS = {
    COMMON_QUESTION_LIST: {"label": "Common questions", "id_prefix": "CQ",
                           "display": "short_label", "fields": [
        {"key": "short_label", "label": "Topic", "type": "text", "required": True},
        {"key": "question", "label": "Question", "type": "textarea", "required": True},
    ]},
}

COMMON_REFERENCE_LISTS = (COMMON_QUESTION_LIST,)

__all__ = ["COMMON_QUESTIONS", "COMMON_QUESTION_LIST", "COMMON_REFERENCE_LISTS",
           "COMMON_REFERENCE_SPECS"]
