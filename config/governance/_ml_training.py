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

Requirement:
``M`` mandatory   ``C`` conditional (the rule is in ``when``)   ``O`` optional
"""
from __future__ import annotations

TRAINING_RUNS_COLLECTION = "training_runs"

MANDATORY, CONDITIONAL, OPTIONAL = "M", "C", "O"

# The six sections, in the order a fit is actually performed.
TRAINING_SECTIONS = (
    ("A", "Task and target"),
    ("B", "Training data"),
    ("C", "Split and validation"),
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
    SCALER_FIT_POINT_LIST: ("Scaler fit points", "SF", ("Train only", "Full dataset"),
                            "Where the scaler was fitted. Fitting on the full dataset leaks."),
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

# Conditional rules, named so ``when`` reads as a sentence and the completeness
# calculation and the form agree about what applies.
WHEN_CLASSIFICATION = "classification"
WHEN_CATEGORICAL = "categorical features present"
WHEN_NEURAL = "neural task"
WHEN_PROBABILITY = "probability consumed downstream"

# The learning tasks each conditional rule fires for. Matched on the STORED value, so
# renaming a task's label in Admin does not change which fields it demands.
CONDITIONAL_TASKS = {
    WHEN_CLASSIFICATION: ("Binary classification", "Multiclass classification"),
    WHEN_NEURAL: ("Sequence", "Image"),
}

# --- The fields -------------------------------------------------------------
# key: (section, label, type, requirement, reference-or-None, when-or-None)
# ``type`` is the ordinary field vocabulary: text | textarea | choice | date | number.
_F = (
    # A. Task and target
    ("learning_task", "A", "Learning task", "choice", MANDATORY, LEARNING_TASK_LIST, None),
    ("target_definition", "A", "Target definition", "textarea", MANDATORY, None, None),
    ("feature_count", "A", "Feature count", "number", MANDATORY, None, None),
    ("intended_use", "A", "Intended use", "textarea", MANDATORY, None, None),
    ("excluded_use", "A", "Excluded use", "textarea", MANDATORY, None, None),
    # B. Training data
    ("snapshot_id", "B", "Snapshot identifier", "text", MANDATORY, None, None),
    ("training_period", "B", "Training period", "text", MANDATORY, None, None),
    ("coverage", "B", "Coverage", "textarea", MANDATORY, None, None),
    ("row_count", "B", "Rows", "number", MANDATORY, None, None),
    ("target_distribution", "B", "Target distribution", "text", CONDITIONAL, None,
     WHEN_CLASSIFICATION),
    ("missing_data", "B", "Missing data treatment", "choice", MANDATORY, MISSING_DATA_LIST, None),
    ("missing_data_columns", "B", "Columns affected", "text", OPTIONAL, None, None),
    ("encoding", "B", "Categorical encoding", "choice", CONDITIONAL, ENCODING_LIST,
     WHEN_CATEGORICAL),
    ("scaling", "B", "Scaling / normalisation", "choice", MANDATORY, SCALING_LIST, None),
    ("scaler_fit_point", "B", "Scaler fitted on", "choice", MANDATORY, SCALER_FIT_POINT_LIST,
     None),
    # C. Split and validation
    ("split_method", "C", "Split method", "choice", MANDATORY, SPLIT_METHOD_LIST, None),
    ("split_proportions", "C", "Split proportions (train/val/test)", "text", MANDATORY, None,
     None),
    ("split_rationale", "C", "Split rationale", "textarea", MANDATORY, None, None),
    ("cv_method", "C", "Cross-validation", "choice", MANDATORY, CV_METHOD_LIST, None),
    ("cv_folds", "C", "Folds (k)", "number", OPTIONAL, None, None),
    ("cv_result", "C", "CV result (mean +/- std)", "text", MANDATORY, None, None),
    ("test_evaluations", "C", "Times the hold-out was evaluated", "number", MANDATORY, None,
     None),
    # D. Fit record
    ("hyperparameters", "D", "Hyperparameters (as fitted)", "textarea", MANDATORY, None, None),
    ("search_method", "D", "Search method", "choice", OPTIONAL, SEARCH_METHOD_LIST, None),
    ("random_seed", "D", "Random seed(s)", "text", MANDATORY, None, None),
    ("determinism", "D", "Determinism", "choice", MANDATORY, DETERMINISM_LIST, None),
    ("run_date", "D", "Run date", "date", MANDATORY, None, None),
    ("run_duration", "D", "Duration", "text", MANDATORY, None, None),
    ("run_hardware", "D", "Hardware", "text", MANDATORY, None, None),
    ("epochs", "D", "Epochs / batch size / early stopping", "text", CONDITIONAL, None,
     WHEN_NEURAL),
    ("convergence_evidence", "D", "Convergence evidence", "text", CONDITIONAL, None, WHEN_NEURAL),
    # E. Performance
    ("primary_metric", "E", "Primary metric", "choice", MANDATORY, METRIC_LIST, None),
    ("metric_train", "E", "Metric on train", "text", MANDATORY, None, None),
    ("metric_cv", "E", "Metric on CV", "text", MANDATORY, None, None),
    ("metric_test", "E", "Metric on test", "text", MANDATORY, None, None),
    ("secondary_metrics", "E", "Secondary metrics", "textarea", CONDITIONAL, None, None),
    ("calibration", "E", "Calibration (curve + Brier)", "text", CONDITIONAL, None,
     WHEN_PROBABILITY),
    ("baseline_kind", "E", "Naive baseline", "choice", MANDATORY, BASELINE_LIST, None),
    ("baseline_value", "E", "Baseline score", "text", MANDATORY, None, None),
    ("challenger", "E", "Challenger comparison", "textarea", MANDATORY, None, None),
    ("segment_performance", "E", "Segment performance", "textarea", MANDATORY, None, None),
    ("worst_segment", "E", "Worst segment", "text", MANDATORY, None, None),
    ("stability", "E", "Stability (bootstrap / repeated CV spread)", "text", OPTIONAL, None,
     None),
    # F. Reproducibility and attestation
    ("code_commit", "F", "Code reference (commit + repo)", "text", MANDATORY, None, None),
    ("environment", "F", "Environment (lockfile)", "text", MANDATORY, None, None),
    ("artefact", "F", "Serialised artefact (path + hash)", "text", MANDATORY, None, None),
    ("rebuild_command", "F", "Rebuild command", "text", MANDATORY, None, None),
    ("reproduced_by", "F", "Independently reproduced by", "text", MANDATORY, None, None),
    ("reproduced_matched", "F", "Reproduction matched", "choice", MANDATORY, None, None),
    ("attested_by", "F", "Owner attestation", "text", MANDATORY, None, None),
    ("attested_date", "F", "Attested on", "date", MANDATORY, None, None),
)

# Derived: the field table the form, the validation and the completeness count read.
TRAINING_FIELD_SPECS = {
    key: {"section": section, "label": label, "type": ftype, "requirement": req,
          **({"reference": ref} if ref else {}),
          **({"when": when} if when else {}),
          **({"options": ("Yes", "No")} if key == "reproduced_matched" else {})}
    for key, section, label, ftype, req, ref, when in _F
}

# The collection one train is stored as. Only ``fit_id`` is required to create one:
# a train is recorded as it is performed and filled in as the evidence arrives, and
# what is still missing is a completeness finding rather than a barrier to recording
# that the fit happened at all.
ML_TRAINING_COLLECTION_SPEC = {
    "label": "Trains", "id_prefix": "TR",
    "fields": [{"key": "fit_id", "label": "Train", "type": "text", "required": True}] + [
        {"key": key, "label": spec["label"], "type": spec["type"],
         **({"reference": spec["reference"]} if spec.get("reference") else {}),
         **({"options": spec["options"]} if spec.get("options") else {})}
        for key, spec in TRAINING_FIELD_SPECS.items()
    ],
}

MANDATORY_FIELDS = tuple(k for k, s in TRAINING_FIELD_SPECS.items()
                         if s["requirement"] == MANDATORY)

# --- Completeness ------------------------------------------------------------
# The state a train's evidence is in. NOT the record's RAG: that is the risk rating,
# Materiality x Complexity through the division's ratified heatmap, moved only by MRC
# sign-off. A thin Training tab is a different fact from a risky model, and a reader
# must be able to tell them apart.
TRAINING_INCOMPLETE = "Incomplete"
TRAINING_QUALIFIED = "Qualified"
TRAINING_COMPLETE = "Complete"

# A hold-out evaluated more often than this has become a validation set: every look
# leaks a little of it into the choices that follow, and the reported test figure
# stops being out-of-sample. Three is a judgement, which is why it is here and not
# in the code.
TEST_EVALUATION_CAP = 3

# A split rationale shorter than this is a label, not an argument. The field exists
# because a random split on spatially correlated data leaks, and "random" is not an
# answer to that.
MIN_RATIONALE_CHARS = 80

# The sections whose mandatory fields must be complete before anything else is worth
# reading: what the model is for, what it was fitted on, and how it was split.
FOUNDATION_SECTIONS = ("A", "B", "C")
