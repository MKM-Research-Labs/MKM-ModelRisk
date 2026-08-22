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
"""How complete a train's evidence is (pure, no I/O).

Computed, never set by hand -- the point of typing the fields was to make this
answerable, and a completeness figure somebody types is an assertion like any other.

The three states are the spec's Red / Amber / Green, named for what they are so they
cannot be mistaken for the record's RAG rating. That is the risk rating, set through
the division's heatmap and moved only by MRC sign-off; this is a statement about
evidence. A model can be Green on risk and Incomplete on training, and a reader has
to be able to see both.
"""
from __future__ import annotations

from typing import Any

from config.governance import TRAINING_FIELD_SPECS
from config.governance._ml_training import (CONDITIONAL_TASKS, MIN_RATIONALE_CHARS,
                                            TEST_EVALUATION_CAP, TRAINING_CLEAN,
                                            TRAINING_QUALIFIED, WHEN_CATEGORICAL,
                                            WHEN_PROBABILITY)


def _recorded(value: Any) -> bool:
    return value not in (None, "") and str(value).strip() != ""


def applies(key: str, train: dict) -> bool:
    """Whether a conditional field applies to this train.

    Matched on the STORED learning task, so renaming a task in Admin changes what the
    screen says and not what the evidence must contain. The two rules that depend on
    the data rather than the task (categorical features present, probability consumed
    downstream) are always offered: the platform cannot know, and a field nobody is
    asked is a field nobody answers.
    """
    spec = TRAINING_FIELD_SPECS.get(key, {})
    when = spec.get("when")
    if not when or when in (WHEN_CATEGORICAL, WHEN_PROBABILITY):
        return True
    return str(train.get("learning_task") or "") in CONDITIONAL_TASKS.get(when, ())


def _qualifications(train: dict) -> list[str]:
    """Populated, but with something a reviewer must be told. The spec's ambers."""
    out = []
    if str(train.get("scaler_fit_point") or "") == "Full dataset":
        out.append("the scaler was fitted on the full dataset, which leaks the test "
                   "set into the fit and inflates the reported metric")
    # The same leak, and a quieter one: nobody thinks of filling in a blank as
    # training on the answer, but a median computed over the whole dataset carries
    # the test set into the fit just as a scaler does.
    if str(train.get("missing_data_fit_point") or "") == "Full dataset":
        out.append("the imputation was fitted on the full dataset, which leaks the "
                   "test set into the fit as surely as a scaler would")
    rationale = str(train.get("split_rationale") or "")
    if _recorded(rationale) and len(rationale.strip()) < MIN_RATIONALE_CHARS:
        out.append("the split rationale is too short to be an argument")
    try:
        if int(train.get("test_evaluations") or 0) > TEST_EVALUATION_CAP:
            out.append(f"the hold-out was evaluated more than {TEST_EVALUATION_CAP} "
                       "times, so it has become a validation set")
    except (TypeError, ValueError):
        pass
    # Only once there is a result worth reproducing. Raising it against a train that
    # has not reported a metric yet is telling somebody off for work they have not
    # finished, which is how a tab teaches people to ignore it.
    if _recorded(train.get("metric_test")) and not _recorded(train.get("reproduced_by")):
        out.append("nobody other than the developer has reproduced the fit")
    elif str(train.get("reproduced_matched") or "") == "No":
        out.append("the independent reproduction did not match")
    return out


def completeness(train: dict | None) -> dict[str, Any]:
    """``{filled, total, state, qualifications}`` for one train.

    ``filled`` of ``total`` is progress, not a score. Fifty-one fields will not all be
    populated on a real estate and saying so on every record helps nobody -- what a
    reviewer needs is the count and, separately, the things recorded that they must be
    told about.
    """
    if not train:
        return {"filled": 0, "total": 0, "state": TRAINING_CLEAN, "qualifications": []}
    applicable = [key for key in TRAINING_FIELD_SPECS if applies(key, train)]
    filled = [key for key in applicable if _recorded(train.get(key))]
    qualifications = _qualifications(train)
    return {"filled": len(filled), "total": len(applicable),
            "state": TRAINING_QUALIFIED if qualifications else TRAINING_CLEAN,
            "qualifications": qualifications}
