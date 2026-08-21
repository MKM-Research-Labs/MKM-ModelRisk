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
from config.governance._ml_training import (CONDITIONAL_TASKS, FOUNDATION_SECTIONS,
                                            MANDATORY, MIN_RATIONALE_CHARS,
                                            TEST_EVALUATION_CAP, TRAINING_COMPLETE,
                                            TRAINING_INCOMPLETE, TRAINING_QUALIFIED,
                                            WHEN_CATEGORICAL, WHEN_PROBABILITY)


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
    rationale = str(train.get("split_rationale") or "")
    if _recorded(rationale) and len(rationale.strip()) < MIN_RATIONALE_CHARS:
        out.append("the split rationale is too short to be an argument")
    try:
        if int(train.get("test_evaluations") or 0) > TEST_EVALUATION_CAP:
            out.append(f"the hold-out was evaluated more than {TEST_EVALUATION_CAP} "
                       "times, so it has become a validation set")
    except (TypeError, ValueError):
        pass
    if not _recorded(train.get("reproduced_by")):
        out.append("nobody other than the developer has reproduced the fit")
    elif str(train.get("reproduced_matched") or "") == "No":
        out.append("the independent reproduction did not match")
    return out


def completeness(train: dict | None) -> dict[str, Any]:
    """``{filled, total, state, missing, qualifications}`` for one train."""
    if not train:
        return {"filled": 0, "total": 0, "state": TRAINING_INCOMPLETE,
                "missing": [], "qualifications": []}
    required = [key for key, spec in TRAINING_FIELD_SPECS.items()
                if spec["requirement"] == MANDATORY or applies(key, train)]
    applicable = [k for k in required if applies(k, train)]
    filled = [k for k in applicable if _recorded(train.get(k))]
    missing = [k for k in applicable
               if k not in filled and TRAINING_FIELD_SPECS[k]["requirement"] == MANDATORY]
    foundation = [k for k in missing
                  if TRAINING_FIELD_SPECS[k]["section"] in FOUNDATION_SECTIONS]
    qualifications = _qualifications(train)
    if foundation:
        state = TRAINING_INCOMPLETE
    elif missing or qualifications:
        state = TRAINING_QUALIFIED
    else:
        state = TRAINING_COMPLETE
    return {"filled": len(filled), "total": len(applicable), "state": state,
            "missing": missing, "qualifications": qualifications}
