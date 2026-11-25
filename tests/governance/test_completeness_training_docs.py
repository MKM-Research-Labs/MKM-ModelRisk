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
"""Which training documents the audit asks of an ML Application and an AI System.

Each training artefact is uploaded beside its field on an ML Application's Training
tab, and the tab shows a field only where it applies to the latest train. A finding
the screen gives no way to close is a penalty, not a gap: MKM-FC-001, a binary
classifier, went overdue on a Convergence document its Training tab would not take.
"""
from __future__ import annotations

from src.governance.ai_system import rebuild_ai_system_view, register_ai_system
from src.governance.completeness.scan import (AI_SYSTEM_KIND, ML_APPLICATION_KIND,
                                              ml_application_doc_categories, scan)
from src.governance.ml_application import (rebuild_ml_application_view,
                                           register_ml_application)

AS_OF = "2026-11-25"
TRAINING = ("Calibration", "Convergence", "Segment analysis")


def _asked(learning_task=None, trains=True):
    runs = [{"fit_id": "1", "learning_task": "Image"},
            {"fit_id": "2", "learning_task": learning_task}] if trains else []
    asked = ml_application_doc_categories({"training_runs": runs})
    return {c for c in TRAINING if c in asked}


def test_classifier_is_not_asked_for_convergence():
    assert _asked("Binary classification") == {"Calibration", "Segment analysis"}


def test_neural_train_is_asked_for_all_three():
    assert _asked("Image") == set(TRAINING)


def test_rule_reads_the_latest_train_not_an_earlier_one():
    """The Training tab shows the most recent fit; an earlier neural one does not
    bring the Convergence panel back."""
    assert "Convergence" not in _asked("Regression")


def test_no_train_yet_is_asked_for_what_a_first_train_offers():
    assert _asked(trains=False) == {"Calibration", "Segment analysis"}


def test_other_categories_are_still_asked():
    assert "Core Documentation" in ml_application_doc_categories({})


def _doc_gaps(kind, entity_id):
    row = next(r for r in scan(AS_OF) if r["entity_kind"] == kind
               and r["entity_id"] == entity_id)
    return {g["key"] for g in row["gaps"]}


def test_scan_asks_an_ml_application_only_what_its_screen_offers():
    register_ml_application(ml_application_id="MLA-1", actor="a",
                            fields={"name": "Retail PD scorecard", "division": "Risk",
                                    "owner": "Owner", "use_case": "Ranks applicants.",
                                    "estimator": "GradientBoostingClassifier"})
    rebuild_ml_application_view()
    gaps = _doc_gaps(ML_APPLICATION_KIND, "MLA-1")
    assert {"Calibration", "Segment analysis"} <= gaps
    assert "Convergence" not in gaps


def test_scan_asks_an_ai_system_for_no_training_documents():
    """An AI System has no trains and no Training tab to file them on."""
    register_ai_system(ai_system_id="AIS-1", actor="a",
                       fields={"name": "Client mail summariser", "division": "Risk",
                               "owner": "Owner", "use_case": "Summarises mail.",
                               "deployment_pattern": "Agentic (tool-using)"})
    rebuild_ai_system_view()
    gaps = _doc_gaps(AI_SYSTEM_KIND, "AIS-1")
    assert not gaps & set(TRAINING)
    assert "Core Documentation" in gaps
