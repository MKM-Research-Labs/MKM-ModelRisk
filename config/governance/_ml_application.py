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
"""The ML Application record: field metadata and collections (coding rule R1).

An ML Application is *a use case for an off-the-shelf estimator*. The estimator
itself is admin vocabulary (see _ml.py); this is the record that says what one
institution does with it, and it is what the committee actually signs off.

The record has two halves, and the split is the whole design:

**The governance half** uses THE SAME FIELD NAMES A MODEL USES. Not similar names
-- the same ones. The completeness audit's clause probes in
``src.governance.completeness.framework`` are field-name lambdas over one
population: ``analysis`` reads tier/materiality/complexity, ``accountability``
reads owner, ``independence`` reads peer_reviewer against owner, ``criteria``
reads division, ``monitoring`` reads next_review_date. Match the names and all of
them count ML Applications with no change at all. Diverge and every probe grows a
per-type branch -- thirteen places to forget one. Same reasoning for the shared
collections below.

**The ML half** is what a model record has no place for: which estimator and
version, why that one rather than a simpler alternative, what it was trained on,
how it performs and how it could be misread.

What this record deliberately does NOT carry, and why:

``dependencies`` / chains   An ML Application has no upstream/downstream graph.
``type`` / ``vendor``       Classification of a model's provenance; an ML
``codebase`` / ``repo``     Application's provenance is its Estimator.
``validation_questions``    It has its own questionnaire (``ml_review_questions``
                            below), seeded from a different admin list.
``version_history``         There is no version. Every fit is a train, recorded in
                            ``training_runs`` with the evidence that fit produced.
``training_data`` etc.      What a fit was trained on and how it performed belongs to
                            the TRAIN that produced it, not to the record. A copy here
                            would be a second answer to the same question, free to
                            disagree with the fit it describes.
``raci_roles``              Accountability for an ML Application's use in production
                            sits on the Product that consumes it, where the RACI
                            operating model already lives. Carrying a second one here
                            would ask the same question twice and let the two answers
                            disagree.
"""
from __future__ import annotations

from config.governance._collections import (COLLECTION_SPECS, EVALUATIONS_COLLECTION,
                                            FAIRNESS_COLLECTION)
from config.governance._inventory import (LIFECYCLE_STAGE_LIST, VALID_COMPLEXITY,
                                          VALID_REVIEW_STATUSES,
                                          VALID_LIFECYCLE_STAGES, VALID_MATERIALITY,
                                          VALID_RAG_RATINGS, VALID_REVIEW_FREQUENCIES,
                                          VALID_VALIDATION_STATUSES, VALIDATION_STATUS_LIST)
from config.governance._ml import ESTIMATOR_LIST
from config.governance._ml_training import (ML_TRAINING_COLLECTION_SPEC,
                                             TRAINING_RUNS_COLLECTION)
from config.governance._review import REVIEW_COLLECTION_SPECS
from config.governance._signoff_collections import SIGNOFF_COLLECTION_SPECS

ML_APPLICATION_ID_PREFIX = "MLA"

# The questionnaire copied onto each record at registration, from the admin
# ml_application_questions list. Named apart from a model's ``validation_questions``
# so the two sets can never be confused for one another on a screen or in a report.
ML_REVIEW_QUESTIONS_COLLECTION = "ml_review_questions"

ML_APPLICATION_FIELD_SPECS = {
    # --- Organisation. Same names as a model's: ``division`` is what the
    #     ``criteria`` probe reads, and what routes the record to its MRC. ---
    "division": {"label": "Division", "type": "text", "group": "Organisation",
                 "reference": "division"},
    "line_of_business": {"label": "Line of Business", "type": "text",
                         "group": "Organisation", "reference": "line_of_business"},
    # An ML Application has code in exactly the sense a model does -- something was
    # fitted, and it lives somewhere. Same names and same references as the inventory.
    "repo_location": {"label": "Repository location", "type": "text",
                      "group": "Organisation"},
    "codebase": {"label": "Codebase", "type": "text", "group": "Organisation",
                 "reference": "codebase"},
    # --- Identity ---
    "name": {"label": "Name", "type": "text", "group": "Identity"},
    "short_name": {"label": "Short name", "type": "text", "group": "Identity"},
    "description": {"label": "Description", "type": "textarea", "group": "Identity"},
    # --- The ML half ---
    # What decision this informs, and what it is not to be used for. First because
    # it is the question every other answer is judged against: a performance figure
    # means nothing until somebody has said what the thing is for.
    "use_case": {"label": "Use case", "type": "textarea", "group": "Estimator and method"},
    # Strict, like a model's ``type``: an ML Application cannot name an estimator
    # nobody has defined in Admin. The version is free text for now -- constraining
    # it to the chosen estimator's own list is a dependent dropdown, which nothing
    # in the reference specs does yet.
    "estimator": {"label": "Estimator", "type": "text", "group": "Estimator and method",
                  "reference": ESTIMATOR_LIST, "strict_reference": True},
    "estimator_version": {"label": "Estimator version", "type": "text", "group": "Estimator and method"},
    # SR 26-2 asks for the reasoning behind a choice, not just the choice. For an ML
    # Application the choice that most needs defending is the estimator: a gradient
    # boosting machine where a logistic regression would have done is the single
    # most common finding against an ML estate.
    "estimator_rationale": {"label": "Why this estimator", "type": "textarea", "group": "Estimator and method"},
    # The estimator names the class; the methodology says what was actually done with
    # it ("Gradient Boosting Classification with binomial deviance loss"), which is
    # more than the class name carries.
    "methodology": {"label": "Methodology", "type": "text", "group": "Estimator and method"},
    "source_module": {"label": "Source module", "type": "text", "group": "Estimator and method"},
    # Who supplies the ML Application itself, as opposed to the estimator it is built
    # on. Strict like a model's: it cannot name a vendor nobody has defined.
    "vendor": {"label": "Vendor", "type": "text", "group": "Estimator and method",
               "reference": "vendor", "strict_reference": True},
    "category": {"label": "Category", "type": "text", "group": "Estimator and method"},
    # Deliberately not a named metric. Area under the curve is a CLASSIFICATION
    # metric; a regression model has RMSE, MAE and R-squared, and much of this
    # estate is regression. The record asks which metric and what it said, so both
    # can answer honestly.
    # Where the output could be read as saying more than it does. Its own field
    # rather than a weakness because it is a risk of USE, not a defect of the
    # model -- the model can be sound and still be misread.
    # --- Classification. The same three dimensions, bands and heatmap a model
    #     carries, so an ML Application's categorisation is challenged on the same
    #     terms -- and so the ``analysis`` and ``evaluation`` probes count it. ---
    "tier": {"label": "Tier", "type": "tier", "group": "Classification"},
    "tier_rationale": {"label": "Tier rationale", "type": "text", "group": "Classification"},
    "materiality": {"label": "Materiality", "type": "choice", "options": VALID_MATERIALITY,
                    "group": "Classification"},
    "materiality_rationale": {"label": "Materiality rationale", "type": "text",
                              "group": "Classification"},
    "complexity": {"label": "Complexity", "type": "choice", "options": VALID_COMPLEXITY,
                   "group": "Classification"},
    "complexity_rationale": {"label": "Complexity rationale", "type": "text",
                             "group": "Classification"},
    "rating_rationale": {"label": "Rating rationale", "type": "text",
                         "group": "Classification"},
    "rag_rating": {"label": "RAG rating", "type": "choice", "options": VALID_RAG_RATINGS,
                   "group": "Classification"},
    # --- Governance. ``owner`` and ``peer_reviewer`` are what the accountability
    #     and independence probes read; the independence check compares the two. ---
    "owner": {"label": "Owner", "type": "text", "group": "Governance", "reference": "people"},
    "peer_reviewer": {"label": "Peer reviewer", "type": "text", "group": "Governance",
                      "reference": "people"},
    "model_owner_role": {"label": "Owner role", "type": "text", "group": "Governance"},
    "status": {"label": "Status", "type": "text", "group": "Governance"},
    # Where the review has got to. Carried so a record migrated from the inventory
    # keeps it; the workflow that MOVES it arrives with the MRC route (phase 4).
    "review_status": {"label": "Review status", "type": "choice",
                      "options": VALID_REVIEW_STATUSES, "group": "Governance"},
    "lifecycle_stage": {"label": "Lifecycle stage", "type": "choice",
                        "options": VALID_LIFECYCLE_STAGES, "group": "Governance",
                        "reference": LIFECYCLE_STAGE_LIST},
    "validation_status": {"label": "Validation status", "type": "choice",
                          "options": VALID_VALIDATION_STATUSES, "group": "Governance",
                          "reference": VALIDATION_STATUS_LIST},
    # A retrain is this record's substantial change, and it is what COSO 15 is
    # evidenced by (the ``change`` probe reads version_history).
    "version": {"label": "Version", "type": "text", "group": "Governance"},
    "review_frequency": {"label": "Review frequency", "type": "choice",
                         "options": VALID_REVIEW_FREQUENCIES, "group": "Governance"},
    # --- Review dates. ``next_review_date`` is the monitoring probe. ---
    "last_review_date": {"label": "Last review", "type": "date", "group": "Review dates"},
    "validation_date": {"label": "Validation date", "type": "date", "group": "Review dates"},
    "recertification_date": {"label": "Recertification", "type": "date",
                             "group": "Review dates"},
    "next_review_date": {"label": "Next review", "type": "date", "group": "Review dates"},
    "mrc_signoff_date": {"label": "MRC sign-off", "type": "date", "group": "Review dates"},
    "mrc_signoff_meeting": {"label": "MRC sign-off meeting", "type": "text",
                            "group": "Review dates"},
    # --- Monitoring. Same name and same intent as a model's: the standing
    #     description of how it is watched. For an ML Application this is where
    #     drift belongs -- the thing most likely to be what goes wrong. ---
    "monitoring_approach": {"label": "Monitoring approach", "type": "textarea",
                            "group": "Monitoring"},
    # --- Testing. The same three flags a model carries; the evidence itself is
    #     filed under the Testing document categories. ---
    "unit_tests": {"label": "Unit tests", "type": "choice", "options": ("Yes", "No"),
                   "group": "Testing"},
    "integration_tests": {"label": "Integration tests", "type": "choice",
                          "options": ("Yes", "No"), "group": "Testing"},
    "benchmark_tests": {"label": "Benchmark tests", "type": "choice",
                        "options": ("Yes", "No"), "group": "Testing"},
}

# The register form's minimum, besides the mandatory id. An ML Application is
# registered before most of it is known -- demanding the narrative up front would
# be answered with placeholders, and an incomplete record is a completeness
# finding, which is where that gap belongs.
ML_APPLICATION_REGISTER_FIELDS = ("name", "division", "owner", "estimator", "use_case")

ML_APPLICATION_COLLECTION_SPECS = {
    # Shared, unchanged, and named identically to a model's -- this is what the
    # ``identification`` and ``treatment`` probes read.
    "assumptions": COLLECTION_SPECS["assumptions"],
    "limitations": COLLECTION_SPECS["limitations"],
    "model_weaknesses": COLLECTION_SPECS["model_weaknesses"],
    "remediation_steps": COLLECTION_SPECS["remediation_steps"],
    # One item per FIT. An ML Application has no versions: the record of change is
    # the sequence of trains, each with its own snapshot, seed, hyperparameters and
    # metrics, so the Trains tab is a view over this rather than a store of its own.
    TRAINING_RUNS_COLLECTION: ML_TRAINING_COLLECTION_SPEC,
    # The feeds it draws on -- for an ML Application, where the training and scoring
    # data comes from. Shared shape, so "which records share a source" is one query.
    "data_sources": COLLECTION_SPECS["data_sources"],
    # Same collection, same name, on all three record types: "who could this
    # disadvantage" is the same question of a model, an ML Application and an AI
    # System, and three shapes would make the estate-wide answer unobtainable.
    FAIRNESS_COLLECTION: COLLECTION_SPECS[FAIRNESS_COLLECTION],
    # What testing actually returned. Same collection on all three record types,
    # because "has this been measured, and what did it say" is one question.
    EVALUATIONS_COLLECTION: COLLECTION_SPECS[EVALUATIONS_COLLECTION],
    "change_history": COLLECTION_SPECS["change_history"],
    "operational_failure_events": COLLECTION_SPECS["operational_failure_events"],
    "actions": COLLECTION_SPECS["actions"],
    # The ML questionnaire, same shape as a model's validation questions but seeded
    # from its own admin list and held under its own name.
    ML_REVIEW_QUESTIONS_COLLECTION: COLLECTION_SPECS["validation_questions"],
    # Borrowed machinery, not reimplemented: the same challenge thread and the same
    # sign-off queue a model and a product use, so an ML Application takes the same
    # trip through the committee and evidences the same clauses.
    **REVIEW_COLLECTION_SPECS,
    **SIGNOFF_COLLECTION_SPECS,
}

# Derived, so validation and the UI cannot drift apart (same rule as the inventory).
ML_APPLICATION_EDITABLE_FIELDS = tuple(ML_APPLICATION_FIELD_SPECS.keys())
ML_APPLICATION_FIELD_CHOICES = {
    key: spec["options"] for key, spec in ML_APPLICATION_FIELD_SPECS.items()
    if spec["type"] == "choice"
}
