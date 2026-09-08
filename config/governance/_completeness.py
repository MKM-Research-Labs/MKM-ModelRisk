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
"""Completeness-audit weights and thresholds (coding rule R1).

The completeness audit asks a different question from the Model Risk Report: not
"what is on the record" but "what is missing from it, and which gap should be
closed first". Every gap is scored rather than merely listed, because a Tier 3
model with no benchmark tests and a Tier 1 Red model with no validation date are
not the same finding, and a flat list of absences invites a reviewer to work the
easy end of it.

This module holds what each missing thing is *worth* before any escalation --
the criticality weights, and the rules deciding which documentation categories
are asked for at all. The escalation factors and severity bands that turn a
weight into a finding live in ``_completeness_scoring``.

Every value here is a judgement an adopting institution is expected to re-set to
its own framework, which is why they are data rather than thresholds in code.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Criticality: how much the absence matters before any escalation.
# ---------------------------------------------------------------------------
# The scale is anchored at both ends: 1.00 is a gap a validator would refuse to
# sign off around, 0.30 is a gap worth recording but not worth chasing. Values
# in between are judgements an adopter is expected to re-set to their own
# framework -- which is why they are data here and not thresholds in code.

DEFAULT_FIELD_CRITICALITY = 0.40

# Fields whose absence is not a finding. ``review_status`` is derived from the
# review dates rather than typed, so an empty one restates a gap already raised
# against ``next_review_date``; counting it twice would inflate the register.
# ``monitoring_approach`` is exempt while the review workflow is being built: it
# lands as an empty field on every existing model, and scoring it on the day the
# tab appears would drop every score for a gap nobody has been asked to fill yet.
# It becomes a finding when the workflow's sign-off gate lands and a review can
# actually be completed (see docs/design/review-workflow.md).
# ``review_status`` is derived from the workflow rather than typed. The rest belong
# to the review itself — the brief an owner writes when a review starts, and the
# "has the documentation been brought up to date" checklist a new version raises —
# so they are empty until a review begins, and scoring them would charge every model
# for a review it has not had. Progress is reported in its own section instead.
EXEMPT_FIELDS = (
    "review_status", "monitoring_approach",
    "review_trigger", "review_scope", "review_due_date",
    "review_docs_updated", "review_sensitivities_updated", "review_test_docs_updated",
)

FIELD_CRITICALITY = {
    # --- Drives the risk rating. Without these the model cannot be rated at
    #     all, so the whole governance record downstream is provisional. ---
    "tier": 1.00,
    "materiality": 0.95,
    "complexity": 0.95,
    "rag_rating": 0.90,
    # --- Accountability. An unowned model has nobody to chase for the rest. ---
    "owner": 0.95,
    "peer_reviewer": 0.75,
    # --- Validation evidence. ---
    "validation_status": 0.90,
    "validation_date": 0.90,
    # --- What the model is and why it was built that way. SR 26-2 asks for the
    #     rationale, not only the choice, so the rationale fields score close to
    #     the choices they explain. ---
    "description": 0.90,
    "methodology": 0.90,
    "methodology_rationale": 0.75,
    "tier_rationale": 0.80,
    "rating_rationale": 0.80,
    # The per-dimension justifications. Below the Mission-Criticality one: that band is the
    # headline classification, while these explain the two heatmap axes.
    "materiality_rationale": 0.65,
    "complexity_rationale": 0.65,
    # --- Review cycle. ---
    "next_review_date": 0.85,
    "last_review_date": 0.70,
    "review_frequency": 0.60,
    "recertification_date": 0.55,
    # --- Committee record. ---
    "mrc_signoff_date": 0.70,
    "mrc_signoff_meeting": 0.65,
    # --- Testing declarations. Benchmarking is the weakest of the three only
    #     because a credible alternative does not exist for every model. ---
    "unit_tests": 0.70,
    "integration_tests": 0.60,
    "benchmark_tests": 0.45,
    # --- Identification and provenance. ---
    "name": 0.60,
    "short_name": 0.50,
    "type": 0.50,
    # Provenance of the model itself: who supplied it. A gap here leaves the
    # record unable to say whether the model is in-house or bought in.
    "vendor": 0.55,
    "category": 0.50,
    "status": 0.65,
    "lifecycle_stage": 0.65,
    "version": 0.45,
    "source_module": 0.50,
    "repo_location": 0.45,
    "codebase": 0.45,
    "division": 0.40,
    "line_of_business": 0.40,
    # --- Product-only fields. ---
    "product": 0.90,
    "product_id": 0.90,
    "analytics_model": 0.85,
    "market_data_model": 0.60,
    "calculating_agent": 0.60,
    "monitoring_approach": 0.70,
    # ``monitoring_results`` was a product-only scalar; monitoring results now live
    # as timestamped uploads under the "Monitoring" document category, whose audit
    # weight is carried by DOC_CRITICALITY["Monitoring"] rather than a field here.
    "notes": 0.30,
}

# ---------------------------------------------------------------------------
# Rules: findings about what a record HOLDS, not about what it lacks.
# ---------------------------------------------------------------------------
# Every other finding in this audit is an absence. A rule finding is a
# contradiction between answers that are both present, which no completeness
# score can see: a model whose peer reviewer is its own owner has both fields
# filled in and scores as fully governed on them. It is also the first record an
# external assessor pulls, so an audit that cannot raise it is reporting the
# estate as better governed than it is.
#
# ``template`` is the instruction, held with the rule rather than in
# REMEDIATION_ACTIONS: each rule is breached in its own way and a generic
# "correct the {item}" tells an owner nothing.
REVIEWER_INDEPENDENCE = "reviewer_independence"

RULE_SPECS = {
    REVIEWER_INDEPENDENCE: {
        "label": "Reviewer independence",
        "detail": "the peer reviewer is the record's own owner",
        # Above validation_date and below owner: a review that was not independent
        # is worth less than no review at all is worth chasing, because the record
        # asserts an assurance it does not have.
        "criticality": 0.85,
        "template": "Name a peer reviewer for the {entity} other than its owner, "
                    "or record why the owner's review is treated as independent.",
    },
}

# ---------------------------------------------------------------------------
# Collections.
# ---------------------------------------------------------------------------
# Collections where empty is a legitimate steady state rather than a gap. An
# empty remediation list means nothing is outstanding; an empty events list means
# nothing has gone wrong. Scoring those as absences would penalise the models
# with the cleanest record, which is exactly backwards.
EXEMPT_COLLECTIONS = (
    "remediation_steps",
    "operational_failure_events",
    "signoff_requests",
    "actions",
    "change_history",
    # Written by the ingest pipe from the producing repo rather than typed by an
    # owner, so its absence is a pipeline finding, not a governance one.
    "field_lineage",
    # --- The review workflow ---------------------------------------------
    # A review is a programme of work with its own timetable, not a field an
    # owner forgot to fill in. Scoring these would mark every model in the estate
    # incomplete from the day the workflow shipped and keep it there until each
    # one had been through a review — a new bar applied retrospectively, which
    # reads as decay rather than as the backlog it is. Progress against them is
    # reported instead, in its own section (see review_programme.py), where "none
    # started yet" is a plan rather than a failure.
    "review_notes",
    "review_progress",
    "review_signoffs",
)

DEFAULT_COLLECTION_CRITICALITY = 0.60

COLLECTION_CRITICALITY = {
    # The nine SR 26-2 questions are the spine of the validation record.
    "validation_questions": 1.00,
    "assumptions": 0.90,
    "limitations": 0.90,
    "model_weaknesses": 0.70,
    "dependencies": 0.65,
    # The feeds a model pulls inputs from — data provenance the SR 26-2 data-
    # quality question turns on. Empty is a genuine gap: every live model
    # consumes data from somewhere.
    "data_sources": 0.65,
    # Below the 0.60 default, and the only weight here set BELOW it. Not because
    # bias matters less than data provenance -- where it applies it matters more --
    # but because it is the one collection that does not apply to every record. A
    # model that ranks retail applicants must answer it; a flood-depth curve has
    # nobody to disadvantage, and scoring the two identically would make the finding
    # noise on half an estate and people stop reading noise.
    #
    # The proper fix is a record saying whether its output bears on people, and there
    # is no such field yet. Until there is, this is deliberately a nudge rather than
    # a cliff: on a 27-record estate it moved mean completeness 0.905 -> 0.892 and
    # pushed nothing below its threshold.
    "fairness_assessments": 0.55,
    # What testing returned, as opposed to the three Yes/No flags saying it happened.
    # Weighted at the same level as the feeds a model draws on: for a record that is
    # scored or relied upon, "what did the test say" is provenance of the same order
    # as "where did the data come from". Above fairness because, unlike bias, this
    # applies to everything on the register -- a curve model has nobody to
    # disadvantage but it still has to have been checked against something.
    "evaluations": 0.65,
    "raci_roles": 0.60,
    "version_history": 0.50,
    "signoff_history": 0.70,
}

# A collection that exists but is only partly worked is its own finding: the nine
# validation questions seeded on registration are present from day one, so
# "recorded" cannot mean "non-empty" for them. Where a collection appears here,
# an item counts only if the named field holds one of the given values.
COLLECTION_ANSWERED = {
    "validation_questions": ("status", ("Addressed",)),
}

# ---------------------------------------------------------------------------
# Documentation.
# ---------------------------------------------------------------------------
DEFAULT_DOC_CRITICALITY = 0.50

DOC_CRITICALITY = {
    "Core Documentation": 1.00,
    "Test Results": 0.90,
    "Analysis": 0.70,
    "Monitoring": 0.65,
    "Unit Test": 0.55,
    "Integration Test": 0.50,
    "Benchmark Test": 0.40,
    "Event Evidence": 0.75,
    "Remediation Evidence": 0.70,
}

# Documentation categories that are never an owner's obligation, so their absence
# is not a finding. "History" holds the copies the platform files automatically
# each time a Model Risk Document is issued: demanding it would raise a finding
# against every model that has never had one issued, which is a statement about
# platform usage rather than about the governance record.
# "Review" holds the reviewer's working papers and "Model Review Report" the signed
# output; both arrive only once a review has run, so they are reported as programme
# progress rather than scored as gaps (see EXEMPT_COLLECTIONS).
EXEMPT_DOC_CATEGORIES = ("History", "Review", "Model Review Report")

# Categories satisfied by a broader evidence pack rather than in their own right.
# The Test Results document reports every unit, integration and benchmark test
# with its assertions; requiring three further uploads restating the same run
# raises three findings per model that no additional evidence would close.
# Where the pack is absent the sub-categories are raised as normal, so a model
# with no testing evidence at all is still reported.
DOC_CATEGORY_SATISFIED_BY = {
    "Unit Test": "Test Results",
    "Integration Test": "Test Results",
    "Benchmark Test": "Test Results",
}

# Values that look like an answer but are not one. A field holding "TBD" is
# indistinguishable from an empty one to a reader of the register, and scoring it
# as recorded lets a record certify itself complete on placeholders -- which is
# the failure this audit exists to catch, not to commit.
PLACEHOLDER_VALUES = (
    "tbd", "tba", "n/a", "na", "none", "nil", "todo", "to do", "pending",
    "unknown", "-", "--", "---", "?", "??", "???", "x", "xxx",
)

# Categories that are only a gap when there is something for them to evidence.
# Each maps to the collection whose open items make the category expected: no
# recorded events means no missing event evidence. This is what stops the audit
# from raising two guaranteed findings against every clean model on the register.
CONDITIONAL_DOC_CATEGORIES = {
    "Event Evidence": "operational_failure_events",
    "Remediation Evidence": "remediation_steps",
}
