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
"""Why each field on a train is asked for (coding rule R1).

Beside the schema rather than inside it only because the two together exceed the
300-line file limit (R2). It is one table logically: ``_ml_training`` merges these in,
and a field without a note is a field nobody can be asked to justify filling in.

Each note answers "why is this required?", not "what is this?". The label already says
what it is. A form that explains itself is a form somebody completes honestly rather
than plausibly -- and several of these are the difference between a number that means
something and a number that does not.
"""
from __future__ import annotations

TRAINING_NOTES = {
    # A. Task and target
    "learning_task": "Fixes what the rest of this tab asks for. A regression is not "
                     "asked for a base rate; a classifier is.",
    "target_definition": "The label AS CONSTRUCTED, in physical units and with its "
                         "thresholds. Two teams can build the same-sounding target and "
                         "predict different things.",
    "feature_count": "How many inputs the fit had. A jump between trains is a change of "
                     "model, not a refresh of one.",
    "intended_use": "What the output may be used for. Every other judgement on this tab "
                    "is made against it.",
    "excluded_use": "What it may NOT be used for. An explicit exclusion can be policed; "
                    "a general warning about misinterpretation cannot.",
    # B. Training data
    "snapshot_id": "An immutable reference to the data as fitted. Without it nothing "
                   "else on this tab can be verified — the numbers cannot be reproduced "
                   "because the data they came from cannot be recovered.",
    "training_period": "What the fit has seen. A model cannot be assumed to hold in "
                       "conditions outside it.",
    "coverage": "Rows, columns, extent and exclusions. What was left out shapes the "
                "result as much as what was kept.",
    "row_count": "The size of the fit. Read alongside the feature count: many features "
                 "on few rows is how a model memorises rather than learns.",
    "target_distribution": "The base rate. On a rare positive class a headline accuracy "
                           "is dominated by the majority and says almost nothing.",
    "missing_data": "Absent values are never absent from the result. Filling with a mean "
                    "invents typical cases; dropping rows can drop a whole segment.",
    "missing_data_columns": "Which columns were affected, so the treatment can be judged "
                            "against the features that mattered.",
    "encoding": "How categories became numbers. Ordinal encoding of an unordered "
                "category asserts an ordering the data does not have.",
    "scaling": "Which transform was applied. It changes what the coefficients and the "
               "importances mean.",
    "scaler_fit_point": "WHERE the scaler was fitted. Fitted on the full dataset it has "
                        "seen the test set, and the reported test metric is inflated.",
    # C. Split and validation
    "split_method": "How the data was divided. This is the single most common way a "
                    "reported metric turns out to be wrong.",
    "split_proportions": "How much was held back. A very small test set produces a "
                         "metric with a confidence interval nobody quotes.",
    "split_rationale": "Why this split does not leak. On spatially or temporally "
                       "correlated data a random split puts the same event on both "
                       "sides, and the model is scored on data it has effectively seen.",
    "cv_method": "How the fit was validated beyond one split. Stratification and "
                 "grouping matter for the same reason the split does.",
    "cv_folds": "How many folds. Too few and the estimate is noisy; too many and it is "
                "expensive without being better.",
    "cv_result": "The mean AND the spread. A single fold score hides instability, and "
                 "the spread is what says whether the headline number is dependable.",
    "test_evaluations": "How many times the hold-out was looked at. Every look leaks a "
                        "little of it into the choices that follow; past a few, the test "
                        "set has quietly become a validation set.",
    # D. Fit record
    "hyperparameters": "The values AS FITTED, not the defaults. A fit cannot be "
                       "reproduced from a description of the algorithm alone.",
    "search_method": "How they were arrived at. An extensive search on a small "
                     "validation set overfits the validation set.",
    "random_seed": "What made this run this run. Without it 'we reran it and got "
                   "something else' has no explanation.",
    "determinism": "Whether it reproduces exactly, approximately, or not at all. An "
                   "honest 'non-deterministic' is worth more than a false claim.",
    "run_date": "When it was fitted. Everything about the world it was fitted in is "
                "dated from here.",
    "run_duration": "How long it took. A retrain that cannot be afforded is a retrain "
                    "that will not happen when it is needed.",
    "run_hardware": "What it ran on. GPU non-determinism and library builds are real "
                    "sources of difference between two runs of the same code.",
    "epochs": "How long it trained, and what stopped it. Early stopping on the test set "
              "is a leak; early stopping on a validation set is not.",
    "convergence_evidence": "The loss curve. It shows whether the fit converged or was "
                            "merely stopped, which the final loss alone does not.",
    # E. Performance
    "primary_metric": "The one number this fit is judged on, named before the results "
                      "are read rather than chosen after them.",
    "metric_train": "Performance on data it was fitted to. On its own it means nothing; "
                    "against the test figure it is the overfitting evidence.",
    "metric_cv": "Performance across folds. The honest middle estimate between train "
                 "and a single test split.",
    "metric_test": "Performance on data it has never seen. The only figure that "
                   "estimates behaviour in use — and only if C is sound.",
    "secondary_metrics": "What the headline metric hides. Accuracy conceals which class "
                         "is being got wrong, and that is usually the one that matters.",
    "calibration": "Whether a stated probability means what it says. A model that ranks "
                   "correctly but is mis-calibrated produces wrong prices and wrong "
                   "capital, and ranking metrics will not show it.",
    "baseline_kind": "The unskilled comparison. Beating a challenger means little if "
                     "neither beats the base rate.",
    "baseline_value": "What the baseline actually scores, on the same metric, so the "
                      "comparison is a comparison.",
    "challenger": "The credible alternative it was tested against, and by how much it "
                  "won. 'Best available' is a claim; this is the evidence.",
    "segment_performance": "How it does by region, peril or period. A headline on a "
                           "pooled dataset is dominated by the easy majority.",
    "worst_segment": "Named, not implied. The worst segment is where the model will "
                     "first do harm, and it is the one nobody volunteers.",
    "stability": "How much the headline moves under resampling. A metric quoted to four "
                 "decimals with a wide spread is three decimals of theatre.",
    # F. Reproducibility and attestation
    "code_commit": "The exact code. A branch name is not a version.",
    "environment": "The library versions. A scikit-learn or TensorFlow minor release "
                   "can change estimator behaviour without changing your code.",
    "artefact": "The fitted object and its hash, so what is scoring in production can be "
                "shown to be what was validated.",
    "rebuild_command": "One line that rebuilds it. If it takes a paragraph, it is not "
                       "reproducible.",
    "reproduced_by": "Somebody other than the developer reran it and got the same "
                     "numbers. This is the field that turns the whole tab from "
                     "assertion into evidence.",
    "reproduced_matched": "Whether it matched. A reproduction that did not is a finding, "
                          "not an omission.",
    "attested_by": "Who stands behind these numbers. A record with no name against it is "
                   "nobody's to defend.",
    "attested_date": "When they did. Attestation is required again on every train, "
                     "because the numbers change.",
}
