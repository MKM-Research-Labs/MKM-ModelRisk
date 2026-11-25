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

Monitoring observations are excluded on EVERY record type, from 2026-11-24, for the
same reason: no screen -- model, ML Application or AI System -- has ever had a
register to record one in, so "Document at least one Monitoring observation entry"
was a finding its owner could not close, only watch go overdue. How a record is
monitored is still asked, as the Monitoring approach field on its review. Should an
intake for observations be built, take the collection out of this list with it.

ML Applications and AI Systems are still scored on fairness and evaluations: there,
they are the point. The collections and categories stay in the model's schema too, so
nothing already recorded is lost; they are only no longer demanded of a model.

The training documents follow the same rule, from 2026-11-25. Each one is uploaded
in the panel beside the field it evidences on an ML Application's Training tab, and
that panel is shown only where the field applies to the latest train: Convergence
evidence is asked of a neural fit (Sequence, Image) and of nothing else. A binary
classifier was being scored on a Convergence document that no screen would accept,
and MKM-FC-001 went overdue on it. So an ML Application is asked for a training
document only where its Training tab offers the panel (src/governance/completeness/
scan.py works that out from the train), and an AI System -- which has no trains and
no Training tab -- is not asked for them at all.
"""

from config.governance._documents import DOC_CATEGORIES, TRAINING_DOC_CATEGORIES

AUDIT_EXCLUDED_COLLECTIONS = ("monitoring_observations",)
MODEL_AUDIT_EXCLUDED_COLLECTIONS = ("fairness_assessments", "evaluations")
MODEL_AUDIT_DOC_CATEGORIES = tuple(c for c in DOC_CATEGORIES
                                   if c not in TRAINING_DOC_CATEGORIES)
AI_SYSTEM_AUDIT_DOC_CATEGORIES = MODEL_AUDIT_DOC_CATEGORIES
