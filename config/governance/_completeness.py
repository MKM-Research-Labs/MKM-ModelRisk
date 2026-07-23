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

The score is a product of one criticality weight and four escalation factors:

    severity = criticality x tier x rag x events x staleness

Multiplicative rather than additive so the factors compound the way the risk
itself does -- an unvalidated model that is also mission critical, also rated
Red, also carrying recent operational failures and also overdue for review is
not four separate small problems. Each factor is centred on 1.0 (no escalation)
so a weight that is not applicable leaves the score untouched, and every input is
published in the report's appendix so an audit professional can reproduce any
severity by hand from the four numbers.

The thresholds below are deliberately in the same idiom as ``RISK_WEIGHTS`` and
``RISK_ACCEPTABLE_AT``: an adopting institution changes its risk appetite here,
in one place, rather than in the scoring code.
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
EXEMPT_FIELDS = ("review_status",)

FIELD_CRITICALITY = {
    # --- Drives the risk rating. Without these the model cannot be rated at
    #     all, so the whole governance record downstream is provisional. ---
    "tier": 1.00,
    "materiality": 0.95,
    "complexity": 0.95,
    "rag_rating": 0.90,
    # --- Accountability. An unowned model has nobody to chase for the rest. ---
    "owner": 0.95,
    "model_owner_role": 0.55,
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
    "monitoring_results": 0.60,
    "notes": 0.30,
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
)

DEFAULT_COLLECTION_CRITICALITY = 0.60

COLLECTION_CRITICALITY = {
    # The nine SR 26-2 questions are the spine of the validation record.
    "validation_questions": 1.00,
    "assumptions": 0.90,
    "limitations": 0.90,
    "model_weaknesses": 0.70,
    "dependencies": 0.65,
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

# Categories that are only a gap when there is something for them to evidence.
# Each maps to the collection whose open items make the category expected: no
# recorded events means no missing event evidence. This is what stops the audit
# from raising two guaranteed findings against every clean model on the register.
CONDITIONAL_DOC_CATEGORIES = {
    "Event Evidence": "operational_failure_events",
    "Remediation Evidence": "remediation_steps",
}

# ---------------------------------------------------------------------------
# Escalation factors. Each is centred on 1.0 -- a factor that does not apply
# leaves the severity where the criticality put it.
# ---------------------------------------------------------------------------

# Tier is the institution's own statement of how much the model matters, so it is
# the primary escalation. Tier 3 is damped rather than zeroed: "not important"
# is not "unaudited".
TIER_WEIGHTS = {1: 1.00, 2: 0.80, 3: 0.60}
UNTIERED_WEIGHT = 0.90          # an untiered model is treated as nearly Tier 1:
                                # the absent tier is itself the reason to look.

RAG_MULTIPLIERS = {"Red": 1.25, "Amber": 1.10, "Green": 1.00}
# An unrated model escalates above Green. A missing rating is not evidence of a
# healthy one, and treating it as Green would let the least-governed models sink
# to the bottom of the remediation list.
UNRATED_MULTIPLIER = 1.15

# Operational failure events in the rolling window (EVENTS_WINDOW_DAYS). A model
# that has actually failed in production carries more weight than one that has
# not, and the effect is capped so a single bad year cannot dominate the ranking.
EVENT_PRESSURE_PER_EVENT = 0.05
EVENT_PRESSURE_CAP = 1.25

# Review staleness, applied against next_review_date. A record that was complete
# at its last review and has since gone unreviewed is a weaker assurance than the
# same record reviewed last month.
STALENESS_STEPS = (
    # (days overdue at or beyond, multiplier)
    (365, 1.20),
    (180, 1.12),
    (90, 1.07),
    (0, 1.03),
)
STALENESS_NONE = 1.00

# ---------------------------------------------------------------------------
# Bands and remediation.
# ---------------------------------------------------------------------------
# (label, score at or above). Ordered worst first; the first match wins.
#
# Calibrated against the escalation range rather than the raw criticality scale,
# which spans 0.30-1.00 while escalation spans 0.60 (Tier 3, Green, clean, in
# date) to 1.875 (Tier 1, Red, five-plus events, a year overdue). The boundaries
# are set so that:
#   - a high-criticality gap on a routine Tier 2 Green record reads High, not
#     Critical -- otherwise "Critical" describes the ordinary case and stops
#     carrying information;
#   - the same gap on a Tier 1 Red record with live events reads Critical;
#   - a low-criticality gap on a Tier 3 record reads Low.
# Set too low, every finding on a badly-kept record bands Critical together and
# the register no longer says what to do first, which is the one thing an audit
# reader needs from it.
SEVERITY_BANDS = (
    ("Critical", 1.00),
    ("High", 0.60),
    ("Medium", 0.35),
    ("Low", 0.00),
)

# Target working days to close, by band. Printed against every finding so the
# register doubles as a remediation plan rather than needing one written after.
REMEDIATION_SLA_DAYS = {
    "Critical": 30,
    "High": 60,
    "Medium": 90,
    "Low": 180,
}

# The recommended action, by gap kind. Phrased as an instruction to the named
# owner, because a finding an auditor cannot hand to somebody is an observation.
REMEDIATION_ACTIONS = {
    "field": "Record {item} on the {entity} record.",
    "collection": "Document at least one {item} entry.",
    "collection_partial": "Complete the outstanding {item} ({detail}).",
    "document": "Upload a document under {item} against the {entity}.",
    "document_broken": "Re-upload under {item}: the record cites a file that is "
                       "not in the document store and cannot be produced.",
}

# A document recorded on the register whose file is absent scores above one never
# uploaded at all. Both leave the same hole in the evidence, but the broken
# reference also asserts to a reader that the evidence exists -- an inventory
# that overstates its own coverage is the more serious audit finding, and it will
# not be caught by anyone reading the register alone.
BROKEN_DOC_ESCALATION = 1.15

# Entity-level roll-up. A record is reported as materially incomplete once its
# weighted completeness falls below this, mirroring RISK_ACCEPTABLE_AT's role of
# turning a continuous score into a statement the committee can act on.
COMPLETENESS_ACCEPTABLE_AT = 0.85
COMPLETENESS_CONDITIONAL_AT = 0.60

# The standard the report cites for its scope. Named here so an adopter
# re-pointing the audit at their own framework changes the citation with it.
AUDIT_BASIS = "SR 26-2 (superseding SR 11-7) and PRA SS1/23"
