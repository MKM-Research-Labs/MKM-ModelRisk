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

"""What the completeness audit scores a MODEL on, where that differs from what a
model can hold (coding rule R1).

A gap the console gives no way to close is not a gap, it is a penalty. On
2026-10-19 the Fairness and Evaluations tabs were removed from the model screen --
no model in the estate used them -- and the ML training documents (Calibration,
Convergence, Segment analysis) have never had a panel on a model's Docs tab. Scoring
a model on them anyway cost every model in the register points it could only win
back by filing placeholders, which the audit itself counts as gaps.

ML Applications and AI Systems are still scored on all of them: there, fairness,
evaluation and training evidence are the point. The collections and categories stay
in the model's schema too, so nothing already recorded is lost; they are only no
longer demanded of a model.
"""

from config.governance._documents import DOC_CATEGORIES, TRAINING_DOC_CATEGORIES

MODEL_AUDIT_EXCLUDED_COLLECTIONS = ("fairness_assessments", "evaluations")
MODEL_AUDIT_DOC_CATEGORIES = tuple(c for c in DOC_CATEGORIES
                                   if c not in TRAINING_DOC_CATEGORIES)
