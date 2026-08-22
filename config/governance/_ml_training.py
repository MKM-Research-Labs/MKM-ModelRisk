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
"""Training evidence for an ML Application: the schema for one train (coding rule R1).

A train is one fit. Not a version -- an ML Application has no versions; the record of
change IS the sequence of trains, each with its own snapshot, seed, hyperparameters
and metrics. So this is one collection item per fit, and the Trains tab is a view
over it rather than a store of its own.

The ordering of the sections is GOVERNANCE, not pedagogy. Split (C) comes before the
preprocessing questions it constrains so that the leakage question is visible on the
page: a scaler or an encoder fitted before the split inflates the reported test metric
and everything below it becomes unreliable.

Everything here is declared once. The section, the type, the vocabulary it draws on
and whether it is required all live in this table, so the form, the validation, the
completeness count and the audit-log field names come from one place and adding a
field is a one-line change.

No field is mandatory. A complete set of fifty-one will not be reached on a real
estate, and a form that opens by declaring most of itself outstanding is a form
somebody stops filling in. What the tab reports instead is how much has been
recorded, and -- separately, and far more usefully -- what has been recorded that a
reviewer must be told about.

A field either APPLIES to a fit or it does not: a regression is not asked for a loss
curve it never produced. That rule lives in ``when``.
"""
from __future__ import annotations

from config.governance._ml_training_notes import (CONDITIONAL_TASKS,  # noqa: F401
                                                  TRAINING_NOTES, WHEN_CATEGORICAL,
                                                  WHEN_CLASSIFICATION, WHEN_NEURAL,
                                                  WHEN_PROBABILITY)

TRAINING_RUNS_COLLECTION = "training_runs"

# The six sections, in the order a fit is actually performed.
TRAINING_SECTIONS = (
    ("A", "Task and target"),
    ("B", "Training data"),
    ("C", "Split, preprocessing and validation"),
    ("D", "Fit record"),
    ("E", "Performance"),
    ("F", "Reproducibility"),
)

# --- Admin vocabularies -----------------------------------------------------
# Every enumeration the spec names becomes an admin-managed list. None ships as a
# fixed tuple: an institution that fits something we never listed must be able to
# say so, and a vocabulary the code owns is one an adopter cannot extend.
#
# Two enumerations from the spec are deliberately absent because they already exist:
# the algorithm IS the Estimator list (a second one would record the same fact twice
# and be free to disagree), and the source dataset IS the Data Source list.
LEARNING_TASK_LIST = "learning_task"
MISSING_DATA_LIST = "missing_data_treatment"
ENCODING_LIST = "categorical_encoding"
SCALING_LIST = "scaling_method"
SCALER_FIT_POINT_LIST = "scaler_fit_point"
SPLIT_METHOD_LIST = "split_method"
CV_METHOD_LIST = "cross_validation_method"
SEARCH_METHOD_LIST = "search_method"
DETERMINISM_LIST = "determinism"
METRIC_LIST = "primary_metric"
BASELINE_LIST = "naive_baseline"

# name -> (label, id prefix, seeded words, what the list is for)
ML_TRAINING_VOCABULARIES = {
    LEARNING_TASK_LIST: ("Learning tasks", "LT",
                         ("Regression", "Binary classification", "Multiclass classification",
                          "Clustering", "Dimensionality reduction", "Sequence", "Image"),
                         "What kind of problem the fit solves. Drives which other fields apply."),
    MISSING_DATA_LIST: ("Missing data treatments", "MD",
                        ("Drop", "Mean", "Median", "Mode", "Model-based", "None"),
                        "How absent values were handled before fitting."),
    ENCODING_LIST: ("Categorical encodings", "CE",
                    ("One-hot", "Ordinal", "Target", "Embedding", "Not applicable"),
                    "How categorical features were represented."),
    SCALING_LIST: ("Scaling methods", "SM",
                   ("Standard", "Min-max", "Robust", "None"),
                   "How features were scaled or normalised."),
    SCALER_FIT_POINT_LIST: ("Fit points", "SF", ("Train only", "Full dataset"),
                            "Where a transform was fitted -- the scaler, the imputer, "
                            "the encoder. Fitting on the full dataset leaks the test "
                            "set into the fit."),
    SPLIT_METHOD_LIST: ("Split methods", "SP",
                        ("Random", "Stratified", "Temporal", "Spatial-group",
                         "Entity-group", "Predefined"),
                        "How the data was divided into train, validation and test."),
    CV_METHOD_LIST: ("Cross-validation methods", "CV",
                     ("None", "K-fold", "Stratified k-fold", "Group k-fold",
                      "Time-series split"),
                     "How the fit was cross-validated."),
    SEARCH_METHOD_LIST: ("Hyperparameter searches", "HS",
                         ("None", "Manual", "Grid", "Random", "Bayesian"),
                         "How the hyperparameters were arrived at."),
    DETERMINISM_LIST: ("Determinism statements", "DT",
                       ("Bit-reproducible", "Reproducible to tolerance", "Non-deterministic"),
                       "How exactly the fit reproduces."),
    METRIC_LIST: ("Performance metrics", "PM",
                  ("ROC-AUC", "PR-AUC", "Accuracy", "F1", "Precision", "Recall",
                   "Brier score", "RMSE", "MAE", "R-squared", "Silhouette"),
                  "The metrics a fit is scored on."),
    BASELINE_LIST: ("Naive baselines", "NB",
                    ("Majority class", "Climatological base rate", "Persistence",
                     "Mean prediction"),
                    "The unskilled comparison a fit must beat before any other."),
}

ML_TRAINING_LISTS = tuple(ML_TRAINING_VOCABULARIES)

# --- Capture at fit time -----------------------------------------------------
# The fields a training run can report for ITSELF. Everything here is a fact about
# the run rather than a judgement about it, so a human retyping it adds nothing but
# the chance of a typo -- and a metric transcribed by hand is a metric nobody can
# tie back to the fit that produced it.
#
# What is deliberately NOT here is what the spec leaves to the owner: the target
# definition, the intended and excluded uses, why the missing data was handled that
# way, why the split does not leak, and what the segment table means. Those are the
# argument, and an argument is not captured, it is made.
CAPTURABLE_FIELDS = (
    "snapshot_id", "row_count", "feature_count",
    "hyperparameters", "search_method", "random_seed", "determinism",
    "run_date", "run_duration", "run_hardware", "epochs",
    "learning_task", "primary_metric", "metric_train", "metric_cv", "metric_test",
    "cv_method", "cv_folds", "cv_result", "split_method", "split_proportions",
    "scaling", "scaler_fit_point", "encoding", "missing_data",
    "missing_data_fit_point",
    "code_commit", "environment", "artefact",
)

# Which fields on a train arrived by capture rather than by hand. Stored on the item
# so a screen can show them as read-only and a reviewer can tell the two apart: a
# field the owner can hand-edit is a field a validator has to verify separately.
CAPTURED_FIELD = "captured_fields"

# --- The fields -------------------------------------------------------------
# key: (section, label, type, reference-or-None, when-or-None)
# ``type`` is the ordinary field vocabulary: text | textarea | choice | date | number.
_F = (
    # A. Task and target
    ("learning_task", "A", "Learning task", "choice", LEARNING_TASK_LIST, None),
    ("target_definition", "A", "Target definition", "textarea", None, None),
    ("features", "A", "Features", "multichoice", "feature", None),
    ("feature_count", "A", "Feature count", "number", None, None),
    ("intended_use", "A", "Intended use", "textarea", None, None),
    ("excluded_use", "A", "Excluded use", "textarea", None, None),
    # B. Training data
    ("snapshot_id", "B", "Snapshot identifier", "text", None, None),
    ("training_period", "B", "Training period", "text", None, None),
    ("coverage", "B", "Coverage", "textarea", None, None),
    ("row_count", "B", "Rows", "number", None, None),
    ("target_distribution", "B", "Target distribution", "text", None,
     WHEN_CLASSIFICATION),
    # C. Split and validation
    ("split_method", "C", "Split method", "choice", SPLIT_METHOD_LIST, None),
    ("split_proportions", "C", "Split proportions (train/val/test)", "text", None,
     None),
    ("split_rationale", "C", "Split rationale", "textarea", None, None),
    # Preprocessing sits AFTER the split, not before it, and that ordering is the
    # governance point rather than a tidy-up. A scaler or an encoder fitted before the
    # split has seen the test set, and the reported test metric is inflated -- so a
    # reader meets "fitted on: full dataset" already knowing what the split was, and
    # can tell in one line whether the numbers below are worth reading.
    ("missing_data", "C", "Missing data treatment", "choice", MISSING_DATA_LIST, None),
    ("missing_data_columns", "C", "Columns affected", "text", None, None),
    ("missing_data_fit_point", "C", "Imputation fitted on", "choice",
     SCALER_FIT_POINT_LIST, None),
    ("encoding", "C", "Categorical encoding", "choice", ENCODING_LIST, WHEN_CATEGORICAL),
    ("scaling", "C", "Scaling / normalisation", "choice", SCALING_LIST, None),
    ("scaler_fit_point", "C", "Scaler fitted on", "choice", SCALER_FIT_POINT_LIST, None),
    ("cv_method", "C", "Cross-validation", "choice", CV_METHOD_LIST, None),
    ("cv_folds", "C", "Folds (k)", "number", None, None),
    ("cv_result", "C", "CV result (mean +/- std)", "text", None, None),
    ("test_evaluations", "C", "Times the hold-out was evaluated", "number", None,
     None),
    # D. Fit record
    ("hyperparameters", "D", "Hyperparameters (as fitted)", "textarea", None, None),
    ("search_method", "D", "Search method", "choice", SEARCH_METHOD_LIST, None),
    ("random_seed", "D", "Random seed(s)", "text", None, None),
    ("determinism", "D", "Determinism", "choice", DETERMINISM_LIST, None),
    ("run_date", "D", "Run date", "date", None, None),
    ("run_duration", "D", "Duration", "text", None, None),
    ("run_hardware", "D", "Hardware", "text", None, None),
    ("epochs", "D", "Epochs / batch size / early stopping", "text", None,
     WHEN_NEURAL),
    ("convergence_evidence", "D", "Convergence evidence", "text", None, WHEN_NEURAL),
    # E. Performance
    ("primary_metric", "E", "Primary metric", "choice", METRIC_LIST, None),
    ("metric_train", "E", "Metric on train", "text", None, None),
    ("metric_cv", "E", "Metric on CV", "text", None, None),
    ("metric_test", "E", "Metric on test", "text", None, None),
    ("secondary_metrics", "E", "Secondary metrics", "textarea", None, None),
    ("calibration", "E", "Calibration (curve + Brier)", "text", None,
     WHEN_PROBABILITY),
    ("baseline_kind", "E", "Naive baseline", "choice", BASELINE_LIST, None),
    ("baseline_value", "E", "Baseline score", "text", None, None),
    ("challenger", "E", "Challenger comparison", "textarea", None, None),
    ("segment_performance", "E", "Segment performance", "textarea", None, None),
    ("worst_segment", "E", "Worst segment", "text", None, None),
    ("stability", "E", "Stability (bootstrap / repeated CV spread)", "text", None,
     None),
    # F. Reproducibility and attestation
    ("code_commit", "F", "Code reference (commit + repo)", "text", None, None),
    ("environment", "F", "Environment (lockfile)", "text", None, None),
    ("artefact", "F", "Serialised artefact (path + hash)", "text", None, None),
    ("rebuild_command", "F", "Rebuild command", "text", None, None),
    ("reproduced_by", "F", "Independently reproduced by", "text", None, None),
    ("reproduced_matched", "F", "Reproduction matched", "choice", None, None),
    ("attested_by", "F", "Owner attestation", "text", None, None),
    ("attested_date", "F", "Attested on", "date", None, None),
)

# Derived: the field table the form, the validation and the completeness count read.
TRAINING_FIELD_SPECS = {
    key: {"section": section, "label": label, "type": ftype,
          "note": TRAINING_NOTES.get(key, ""),
          **({"reference": ref} if ref else {}),
          **({"when": when} if when else {}),
          **({"options": ("Yes", "No")} if key == "reproduced_matched" else {})}
    for key, section, label, ftype, ref, when in _F
}

# The collection one train is stored as. Only ``fit_id`` is required to create one:
# a train is recorded as it is performed and filled in as the evidence arrives, and
# what is still missing is a completeness finding rather than a barrier to recording
# that the fit happened at all.
ML_TRAINING_COLLECTION_SPEC = {
    "label": "Trains", "id_prefix": "TR",
    "fields": [{"key": "fit_id", "label": "Train", "type": "text", "required": True},
               {"key": CAPTURED_FIELD, "label": "Captured automatically", "type": "text",
                "hidden": True}] + [
        {"key": key, "label": spec["label"], "type": spec["type"],
         **({"reference": spec["reference"]} if spec.get("reference") else {}),
         **({"options": spec["options"]} if spec.get("options") else {})}
        for key, spec in TRAINING_FIELD_SPECS.items()
    ],
}



# --- Artefacts ---------------------------------------------------------------
# Which field each artefact category is filed against. The evidence is the plot or
# the table; the field beside it carries the reading of it. A field with a number in
# it and no artefact behind it is an assertion, which is what these turn into
# evidence -- so completeness counts the artefact, not the sentence.
TRAINING_ARTEFACTS = {
    "calibration": "Calibration",
    "convergence_evidence": "Convergence",
    "segment_performance": "Segment analysis",
}

# --- Completeness ------------------------------------------------------------
# The state a train's evidence is in. NOT the record's RAG: that is the risk rating,
# Materiality x Complexity through the division's ratified heatmap, moved only by MRC
# sign-off. A thin Training tab is a different fact from a risky model, and a reader
# must be able to tell them apart.
# What a train's evidence says, and it is never a pass mark. Either something has
# been recorded that a reviewer must be told about, or nothing has.
TRAINING_QUALIFIED = "Qualified"
TRAINING_CLEAN = "No findings"

# A hold-out evaluated more often than this has become a validation set: every look
# leaks a little of it into the choices that follow, and the reported test figure
# stops being out-of-sample. Three is a judgement, which is why it is here and not
# in the code.
TEST_EVALUATION_CAP = 3

# A split rationale shorter than this is a label, not an argument. The field exists
# because a random split on spatially correlated data leaks, and "random" is not an
# answer to that.
MIN_RATIONALE_CHARS = 80


