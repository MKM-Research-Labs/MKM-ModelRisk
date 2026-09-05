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
"""Tests for the per-ML-Application ML Application Document.

The ML sibling of the Model Risk Document, and the assertions that matter are the
ones about what it must NOT do: drop an unanswered question, bury the training
findings, or print the trains in the order they happened rather than newest first.
"""
from __future__ import annotations

from config.governance import ML_REVIEW_QUESTIONS_COLLECTION, TRAINING_RUNS_COLLECTION
from src.governance.ml_application.document import (build_ml_application_document_tex,
                                                    render_ml_application_document_pdf)

TRAIN = {
    "item_id": "TR-001", "fit_id": "fit-2026-02", "learning_task": "Classification",
    "split_method": "Stratified", "split_rationale": "Split by application month so a "
    "later cohort never trains the model that scores it.",
    "scaler_fit_point": "Full dataset", "metric_test": "0.81",
    "primary_metric": "AUC",
}

RECORD = {"ml_application_id": "MLA-0001", "data": {
    "name": "Retail PD scorecard",
    "description": "Ranks retail applicants by probability of default.",
    "division": "Risk", "owner": "David K Kelly",
    "estimator": "GradientBoostingClassifier",
    "tier": 2, "rag_rating": "Green",
    "review_status": "Remediation", "next_review_date": "2020-01-01",
    "limitations": [{"description": "UK book only", "impact": "Medium"}],
    ML_REVIEW_QUESTIONS_COLLECTION: [
        {"item_id": "Q-001", "short_label": "Training data",
         "question": "What was it fitted on?", "status": "Not Addressed"},
    ],
    TRAINING_RUNS_COLLECTION: [
        {"item_id": "TR-000", "fit_id": "fit-2025-11", "learning_task": "Classification"},
        TRAIN,
    ],
    "training_completeness": {"filled": 7, "total": 40, "qualifications": [
        "the scaler was fitted on the full dataset, which leaks the test set into the "
        "fit and inflates the reported metric"]},
}}

SETTINGS = {"fields": {"org_name": "MKM"}}


def _tex(record=RECORD, as_of="2026-06-22"):
    return build_ml_application_document_tex(record, SETTINGS, as_of)


def test_document_is_about_one_ml_application_and_names_it_on_the_title_page():
    tex = _tex()
    assert "MLA-0001 --- Retail PD scorecard" in tex
    assert "ML Application Document" in tex
    assert tex.strip().endswith("\\end{document}")


def test_document_promotes_the_dossier_to_top_level_sections():
    """The record is the whole document, so its parts are sections in their own
    right — the same shape the Model Risk Document takes."""
    tex = _tex()
    for part in ("Overview", "Estimator and method", "Classification", "Governance",
                 "Training evidence", "Trains", "Review questions", "Limitations",
                 "Attached documents"):
        assert "\\section{" + part + "}" in tex


def test_use_case_and_estimator_lead_the_classification_that_follows():
    """A reader arrives asking what the thing is for and what it is built on, so
    that ordering is the document's argument and not a cosmetic choice."""
    tex = _tex()
    assert tex.index("\\section{Estimator and method}") < \
        tex.index("\\section{Classification}")
    assert tex.index("\\section{Classification}") < tex.index("\\section{Trains}")


def test_the_review_due_status_is_derived_and_not_the_stored_workflow_status():
    tex = _tex()
    assert "Remediation" in tex                        # the stored workflow status
    assert "Review due (at document date)" in tex
    assert "Overdue" in tex                            # derived from the 2020 date


def test_the_findings_a_reviewer_must_be_told_about_are_stated_not_summarised():
    """The reason the training tab is typed at all: a document carrying every field
    but not the leak has buried the line that decides what the metrics mean."""
    tex = _tex()
    assert "7 of 40 fields recorded" in tex
    assert "A reviewer must be told" in tex
    assert "leaks the test set into the fit" in tex


def test_a_fit_with_nothing_worth_flagging_says_so_rather_than_going_quiet():
    record = {**RECORD, "data": {**RECORD["data"],
                                 "training_completeness": {"filled": 40, "total": 40,
                                                           "qualifications": []}}}
    tex = _tex(record)
    assert "Nothing recorded here that a reviewer must be told about" in tex


def test_a_record_that_has_never_been_fitted_omits_the_evidence_section():
    """No train, nothing to qualify: an empty findings table would read as a clean
    bill of health for a fit that never happened."""
    data = {k: v for k, v in RECORD["data"].items()
            if k not in ("training_completeness", TRAINING_RUNS_COLLECTION)}
    tex = _tex({**RECORD, "data": data})
    assert "\\section{Training evidence}" not in tex
    assert "\\section{Trains}" in tex                   # still stated, as not recorded


def test_trains_are_newest_first_and_labelled_by_the_fit_that_reported_them():
    tex = _tex()
    assert tex.index("\\subsection{Train fit-2026-02}") < \
        tex.index("\\subsection{Train fit-2025-11}")


def test_a_train_is_laid_out_in_the_numbered_sections_it_was_recorded_under():
    """A flat run of fifty-three fields loses the ordering the sections carry — the
    split is stated before the preprocessing that depends on it."""
    tex = _tex()
    assert "\\subsection{1. Task and target}" in tex
    assert tex.index("\\subsection{3. Split, preprocessing and validation}") < \
        tex.index("\\subsection{5. Performance}")


def test_an_unanswered_review_question_is_stated_as_unanswered():
    """A dossier that silently drops what nobody filled in reads as a complete
    record of a complete model."""
    tex = _tex()
    assert "Not Addressed" in tex


def test_a_record_with_no_description_says_so_rather_than_opening_on_a_blank():
    data = {k: v for k, v in RECORD["data"].items() if k != "description"}
    tex = _tex({**RECORD, "data": data})
    assert "\\section{Overview}" in tex
    assert "Not recorded" in tex


def test_render_ml_application_document_pdf(monkeypatch):
    monkeypatch.setattr("src.governance.mrc.pack.compile_tex",
                        lambda tex, assets=None: b"%PDF-stub")
    assert render_ml_application_document_pdf(
        RECORD, {"fields": {}}, "2026-06-22") == b"%PDF-stub"
