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
"""modelrisk — report a training run to the ML Application register.

Import this in the code that fits the model. Everything the run knows about itself
goes over on its own; you are left the fields that require judgement.

    from modelrisk import capture

    with capture("MKM-FC-001", fit_id="2026-03-03-v1.2") as run:
        run.data(snapshot_id=snap.sha, row_count=len(X), feature_count=X.shape[1])
        model = GradientBoostingClassifier(**params).fit(X_train, y_train)
        run.fit(model, seed=SEED)
        run.score("ROC-AUC", train=auc_train, cv=auc_cv, test=auc_test)

The run posts on exit, including after an exception -- a fit that fell over is a fact
about the fit, and a train recorded as incomplete is better than one nobody knows
happened. Re-reporting the same ``fit_id`` updates that train rather than adding
another.

Deliberately NOT accepted: the target definition, the intended and excluded uses, why
the missing data was handled that way, why the split does not leak, what the segment
table means. Those are the argument, and an argument is not captured, it is made.
"""
from modelrisk.capture import capture, TrainingRun  # noqa: F401

__all__ = ["capture", "TrainingRun"]
