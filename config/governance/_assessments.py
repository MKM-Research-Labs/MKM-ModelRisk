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
"""Assessment collections: what was MEASURED about a record.

Fairness and evaluations, held together and apart from ``_collections`` because they
are the same kind of thing and the rest of that module is not. Everything there
describes a record — its assumptions, its feeds, its dependencies, what it is meant
to do. These two say what somebody found when they went and checked.

That distinction is the reason both exist. ``benchmark_tests: Yes`` records that
testing happened and nothing else: not what was tested, against what, what it found,
or when. A committee cannot challenge a Yes. Nor can it challenge "we assess for
bias" — only "we measured demographic parity across age bands in July and it held
within 5pp".

Both are carried by the model inventory, ML Applications and AI Systems under one
name each, so "what has this firm actually measured" is one query rather than three.
"""
from __future__ import annotations

# What kind of exercise an evaluation was. Kept apart rather than collapsed into one
# "testing" bucket because they answer different questions and fail differently: a
# held-out score says whether it generalises, a benchmark says whether it beats the
# obvious alternative, a red team says whether it can be made to misbehave, and a
# judge score says whether another model thinks the output is any good.
VALID_EVALUATION_KINDS = ("Held-out performance", "Benchmark against a baseline",
                          "Adversarial / red team", "LLM-as-a-judge",
                          "Human review", "Reproducibility check")
# Blank is allowed and means "no verdict was reached", which is different from a fail.
# An exploratory red-team run produces findings without a pass mark, and forcing one
# would make somebody invent it.
VALID_EVALUATION_VERDICTS = ("Passed", "Passed with caveats", "Failed", "Inconclusive")

# The verdict that stands in the way of a review sign-off, on the same reasoning as
# the fairness register's: a failed evaluation is answered by running it again and
# saying what changed, not by signing past it. "Passed with caveats" does not block --
# the caveats are what the record of challenge is for -- and "Inconclusive" does not
# either, for the reason a fairness assessment's does not.
ADVERSE_EVALUATION_VERDICT = "Failed"

# The reviewer's reading of what a fairness measurement showed. Separate from
# ``finding``, which stays prose, for exactly the reason ``evaluations`` separates
# ``passed`` from ``result``: "no disparity above the threshold" and "not measured" are
# different answers and a boolean collapses them -- but a register with no verdict at
# all cannot be acted on either, and this one had none. Blank is allowed and means no
# verdict was reached, which is what every row recorded before this existed carries.
VALID_FAIRNESS_VERDICTS = ("No disparity found", "Within tolerance",
                           "Disparity found", "Inconclusive")

# The verdict that stands in the way of a review sign-off. One value, not a severity
# scale: the question the gate asks is "does a measured disparity stand unanswered",
# and grading it would only invite the grade to be argued down. "Inconclusive" is
# deliberately NOT here -- it says nobody knows yet, which is a reason to keep
# measuring rather than a finding to remediate, and blocking on it would train people
# to avoid the word.
ADVERSE_FAIRNESS_VERDICT = "Disparity found"

FAIRNESS_COLLECTION = "fairness_assessments"
EVALUATIONS_COLLECTION = "evaluations"

ASSESSMENT_COLLECTION_SPECS = {
    # Who could be disadvantaged by this record's output, and what was actually
    # measured about it. A COLLECTION rather than a paragraph, because the question is
    # asked per attribute and the answers differ: a model may be tested against age
    # and never against postcode-as-a-proxy, and a single "we assessed fairness" field
    # cannot say which. One row per attribute is what makes "which attributes has
    # anything been measured against" a query rather than a reading exercise.
    #
    # ``attribute`` is free text on purpose. Which characteristics are protected is a
    # matter of law and it differs by jurisdiction -- a fixed list of ours would be
    # wrong somewhere on its first day, and an institution that needs a controlled
    # vocabulary can make it an admin list without this shape changing.
    #
    # ``finding`` is deliberately not a pass/fail. "No disparity above the threshold"
    # and "not measured" are different answers, and a boolean collapses them. The
    # verdict is carried separately, as it is on an evaluation -- prose for what was
    # seen, a stated conclusion about it, and neither standing in for the other. A
    # register with findings and no conclusions is a notepad: nothing downstream can
    # act on a paragraph, so nothing did.
    FAIRNESS_COLLECTION: {"label": "Fairness assessment", "id_prefix": "FAIR", "fields": [
        {"key": "attribute", "label": "Attribute or group", "type": "textarea",
         "required": True},
        {"key": "how_assessed", "label": "How it was assessed", "type": "textarea"},
        {"key": "metric", "label": "Metric", "type": "textarea"},
        {"key": "finding", "label": "What it showed", "type": "textarea"},
        {"key": "verdict", "label": "Verdict", "type": "choice",
         "options": VALID_FAIRNESS_VERDICTS},
        # Stacked under the verdict rather than given a column of its own: a date is
        # narrow and a verdict is not, and the two read together anyway — "within
        # tolerance, as at August".
        {"key": "assessed_on", "label": "Assessed on", "type": "date", "stacked": True,
         "default_today": True},
    ]},
    # One row per evaluation run: what was tested, against what, what came back.
    #
    # ``kind`` separates things that are genuinely different exercises and would
    # otherwise be averaged into meaninglessness -- a held-out accuracy figure, a
    # benchmark against a baseline, an adversarial red-team attempt and an
    # LLM-as-a-judge score answer different questions and fail in different ways.
    #
    # ``result`` is prose, not a number. Half of what matters is not a scalar: "held
    # at 0.81 AUC but degraded sharply below 200 observations per segment" is the
    # finding, and a numeric column would keep the 0.81 and lose the sentence that
    # makes it actionable. ``passed`` carries the verdict separately for the cases
    # where there IS one, and is deliberately allowed to be blank -- an exploratory
    # red-team run has a finding and no pass mark.
    #
    # ``dataset`` and ``performed_on`` are what make a result checkable later: a
    # metric with no evaluation set and no date cannot be reproduced or aged.
    EVALUATIONS_COLLECTION: {"label": "Evaluation", "id_prefix": "EVAL", "fields": [
        {"key": "kind", "label": "Kind", "type": "choice", "options": VALID_EVALUATION_KINDS,
         "required": True},
        {"key": "dataset", "label": "Evaluated against", "type": "textarea"},
        {"key": "metric", "label": "Metric", "type": "textarea"},
        {"key": "result", "label": "What it returned", "type": "textarea"},
        {"key": "passed", "label": "Verdict", "type": "choice",
         "options": VALID_EVALUATION_VERDICTS},
        {"key": "performed_on", "label": "Performed on", "type": "date",
         "stacked": True, "default_today": True},
    ]},
}
