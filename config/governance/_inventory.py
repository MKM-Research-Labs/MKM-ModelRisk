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
"""Model-inventory scalar fields and risk vocabulary (coding rule R1).

``MODEL_FIELD_SPECS`` is the single source of truth for the inventory's scalar
fields: each entry carries a label, an input type, its group (for the grouped
detail view), and — for choice fields — its options. ``EDITABLE_FIELDS`` and
``FIELD_CHOICES`` are derived from it so validation and the UI never drift apart.
"""
from config.governance._review import (REVIEW_FIELD_SPECS,
                                       VALID_REVIEW_STATUSES,  # noqa: F401 (re-export)
                                       VALID_REVIEW_TRIGGERS)

VALID_RAG_RATINGS = ("Green", "Amber", "Red")
VALID_VALIDATION_STATUSES = (
    "Initial",
    "Pending",
    "Validated",
    "Conditionally Approved",
    "Rejected",
)
VALID_MATERIALITY = ("Low", "Medium", "High")
VALID_COMPLEXITY = ("Low", "Medium", "High")
# The admin vocabulary behind the lifecycle field. Named here, beside the field
# that uses it, because the reference specs import from this module and not the
# other way round.
LIFECYCLE_STAGE_LIST = "lifecycle_stage"
VALIDATION_STATUS_LIST = "validation_status"
# "Pre Development" is where a model sits once it is proposed but not yet started --
# a submitted bid, an approved business case awaiting kickoff. It is first because the
# tuple is read in order and the order is what every dropdown offers.
#
# Note this tuple is the VALIDATION list as well as the seed for the admin reference
# list. Adding a stage to the reference list alone changes what the dropdown shows but
# not what the command will accept, and the write is then refused by _validate_field.
VALID_LIFECYCLE_STAGES = ("Pre Development", "Development", "Validation",
                          "Production", "Retired")
VALID_REVIEW_FREQUENCIES = ("Monthly", "Quarterly", "Semi-annual", "Annual")
TIER_MIN = 1
TIER_MAX = 3

# Fields captured on the registration form (besides the mandatory id + name).
# Company is NOT here — it comes from the org-scope selector in the header, so a
# model is defined by its ID within the selected Company. Division and Line of Business
# are captured on the form.
REGISTER_FIELDS = (
    "division", "line_of_business", "repo_location", "codebase", "type", "vendor",
    "category", "tier", "owner",
)

# Ordered scalar field specifications. type is one of: text | choice | date | tier.
MODEL_FIELD_SPECS = {
    # --- Organisation (division / line of business are backed by admin-managed
    #     reference lists; every model belongs to the singleton institution
    #     whose name is on the MRC settings under org_name). ---
    "division": {"label": "Division", "type": "text", "group": "Organisation", "reference": "division"},
    "line_of_business": {"label": "Line of Business", "type": "text", "group": "Organisation", "reference": "line_of_business"},
    # What the record is FOR, as this division's MRC has carved its estate up --
    # a different question from ``type``, which is what it IS. ``options`` is empty
    # because there is no firm-wide list: a division's groups come from its ratified
    # policy and are resolved per record (config/governance/_functional_groups).
    "functional_group": {"label": "Functional Group", "type": "choice", "options": (),
                         "group": "Organisation"},
    # The canonical repository for a codebase is carried on the admin ``codebase``
    # entry; this field holds the value chosen there, so the two cannot drift.
    "repo_location": {"label": "Repository location", "type": "text", "group": "Organisation"},
    "codebase": {"label": "Codebase", "type": "text", "group": "Organisation",
                 "reference": "codebase"},
    # --- Classification ---
    "name": {"label": "Name", "type": "text", "group": "Classification"},
    "short_name": {"label": "Short name", "type": "text", "group": "Classification"},
    "description": {"label": "Description", "type": "text", "group": "Classification"},
    # Admin-managed (reference "model_type") rather than a fixed vocabulary: an
    # adopter classifies its own estate. Product bindings read the entry's
    # binding_role, never this name.
    #
    # ``strict_reference`` keeps the closed vocabulary this field had when its
    # options were hardcoded: the values are admin-managed now, but a model still
    # cannot be typed as something nobody has defined. Reference fields without
    # the flag (owner, division) stay open — they hold names that predate the
    # lists, and rejecting those would block every edit to an existing record.
    "type": {"label": "Type", "type": "text", "group": "Classification",
             "reference": "model_type", "strict_reference": True},
    # Who supplies the model itself — the institution's own name for a model it
    # built, or the firm it bought it from. Strict like ``type``: a model cannot
    # name a vendor nobody has defined in Admin.
    "vendor": {"label": "Vendor", "type": "text", "group": "Classification",
               "reference": "vendor", "strict_reference": True},
    "category": {"label": "Category", "type": "text", "group": "Classification"},
    "tier": {"label": "Tier", "type": "tier", "group": "Classification"},
    "tier_rationale": {"label": "Tier rationale", "type": "text", "group": "Classification"},
    # One justification per risk dimension. The owner picks the band; SR 26-2 asks for the
    # reasoning behind the choice, and Mission Criticality had the only rationale field —
    # so Materiality and Complexity, which place the model on the heatmap, carried none.
    "materiality_rationale": {
        "label": "Materiality rationale", "type": "text", "group": "Classification",
    },
    "complexity_rationale": {
        "label": "Complexity rationale", "type": "text", "group": "Classification",
    },
    # The model owner's narrative for the overall risk rating (materiality +
    # complexity + tier), shown beneath Tier on the overview.
    "rating_rationale": {"label": "Rating rationale", "type": "text", "group": "Classification"},
    "materiality": {
        "label": "Materiality", "type": "choice",
        "options": VALID_MATERIALITY, "group": "Classification",
    },
    "complexity": {
        "label": "Complexity", "type": "choice",
        "options": VALID_COMPLEXITY, "group": "Classification",
    },
    # --- Methodology ---
    "methodology": {"label": "Methodology", "type": "text", "group": "Methodology"},
    "methodology_rationale": {
        "label": "Methodology rationale", "type": "text", "group": "Methodology",
    },
    "source_module": {"label": "Source module", "type": "text", "group": "Methodology"},
    # --- Governance ---
    "owner": {"label": "Owner", "type": "text", "group": "Governance", "reference": "people"},
    # ``model_owner_role`` was retired on 2026-09-08. It held the owner's job title —
    # a fact about the PERSON, not about the record — so every model that person owned
    # carried its own copy, all of which went stale together when they changed role.
    # Admin > People already answers it, with ``roles`` ratified at a meeting, so this
    # was an ungoverned second copy of a governed fact. Nothing read it but a
    # completeness weight, which meant the audit marked a record down for not
    # duplicating something it could already look up.
    #
    # Removed from the specs AND from the scoring together. It was once dropped from
    # the detail screens alone, which left it uneditable while the audit still expected
    # it — the failure this note exists to stop somebody repeating.
    "peer_reviewer": {
        "label": "Peer reviewer", "type": "text", "group": "Governance", "reference": "people",
    },
    "status": {"label": "Status", "type": "text", "group": "Governance"},
    "lifecycle_stage": {
        "label": "Lifecycle stage", "type": "choice",
        "options": VALID_LIFECYCLE_STAGES, "group": "Governance",
        "reference": LIFECYCLE_STAGE_LIST,
    },
    "version": {"label": "Version", "type": "text", "group": "Governance"},
    "validation_status": {
        "label": "Validation status", "type": "choice",
        "options": VALID_VALIDATION_STATUSES, "group": "Governance",
        "reference": VALIDATION_STATUS_LIST,
    },
    # Where the review has got to. Set by the review workflow's interim approvals,
    # not typed here (see config/governance/_review.py).
    "review_status": {
        "label": "Review status", "type": "choice",
        "options": VALID_REVIEW_STATUSES, "group": "Governance",
    },
    "rag_rating": {
        "label": "RAG rating", "type": "choice",
        "options": VALID_RAG_RATINGS, "group": "Governance",
    },
    "review_frequency": {
        "label": "Review frequency", "type": "choice",
        "options": VALID_REVIEW_FREQUENCIES, "group": "Governance",
    },
    # --- Review dates ---
    "last_review_date": {"label": "Last review", "type": "date", "group": "Review dates"},
    "next_review_date": {"label": "Next review", "type": "date", "group": "Review dates"},
    "mrc_signoff_date": {"label": "MRC sign-off", "type": "date", "group": "Review dates"},
    # The meeting that granted the MRC sign-off — shown (in place of the date) as
    # the "MRC sign-off" value once a committee approves the rating.
    "mrc_signoff_meeting": {"label": "MRC sign-off meeting", "type": "text", "group": "Review dates"},
    "recertification_date": {"label": "Recertification", "type": "date", "group": "Review dates"},
    "validation_date": {"label": "Validation date", "type": "date", "group": "Review dates"},
    # --- Review ---
    # The workflow's own fields, shared with every record type that carries the
    # review (config/governance/_review.py). Defined there rather than here so a
    # model, an ML Application and an AI System cannot drift apart on them.
    **REVIEW_FIELD_SPECS,
    # Stage 5 of the review: how the model will be watched once it is in use, in
    # the owner's and reviewer's own words. Deliberately a narrative rather than a
    # register of metrics and thresholds — an approach is agreed in sentences long
    # before anyone can name the numbers. It structures later if it needs to,
    # without disturbing the workflow around it.
    "monitoring_approach": {
        "label": "Monitoring approach", "type": "textarea", "group": "Review",
    },
    # --- Testing ---
    "unit_tests": {
        "label": "Unit tests", "type": "choice", "options": ("Yes", "No"), "group": "Testing",
    },
    "integration_tests": {
        "label": "Integration tests", "type": "choice", "options": ("Yes", "No"), "group": "Testing",
    },
    "benchmark_tests": {
        "label": "Benchmark tests", "type": "choice", "options": ("Yes", "No"), "group": "Testing",
    },
}

# Which record field carries which risk dimension, and which field justifies it.
# The three dimensions are structural, so this mapping is too — but nothing here
# says what a dimension is CALLED. That is the division's policy's to say, and any
# surface showing a dimension asks the policy rather than spelling it out, so a
# rename reaches every screen and every document at once.
RISK_DIMENSION_FIELDS = {
    "tier": "mission_criticality", "materiality": "materiality", "complexity": "complexity",
}
RISK_RATIONALE_FIELDS = {
    "tier_rationale": "mission_criticality", "materiality_rationale": "materiality",
    "complexity_rationale": "complexity",
}

# Human-readable tier descriptors (shown next to the tier badge).
# Three tiers by criticality (Tier 4/5 are not used).
TIER_LABELS = {1: "Mission critical", 2: "Important", 3: "Not important"}

# The nine SR 26-2 / Handbook validation questions seeded on registration.
# (SR 26-2 supersedes SR 11-7; the questions are unchanged.)
SR262_QUESTIONS = (
    {"short_label": "Ronseal Test", "question": "Does the model do what it says on the tin?"},
    {"short_label": "Accuracy & Stability",
     "question": "Does the model provide timely, accurate and stable results?"},
    {"short_label": "Resource Usage",
     "question": "Does the model consume excessive computational resources?"},
    {"short_label": "Override Controls", "question": "Are there controls over manual overrides?"},
    {"short_label": "Data Quality",
     "question": "Is the input data accurate, complete and appropriate?"},
    {"short_label": "Assumptions",
     "question": "Are the model's assumptions documented and justified?"},
    {"short_label": "Limitations",
     "question": "Are the model's limitations understood and monitored?"},
    {"short_label": "Benchmarking",
     "question": "Has the model been benchmarked against credible alternatives?"},
    {"short_label": "Independent Validation",
     "question": "Has the model been independently validated?"},
)
DEFAULT_VQ_STATUS = "Not Addressed"

# W4a — Materiality × Complexity → RAG heatmaps, one per tier. The owner sets
# the two axes on the model; the cell for the model's tier is the primary risk
# rating, supplemented by the composite breakdown above. Rows are materiality
# (High/Medium/Low), columns complexity (Low/Medium/High).
#
# The tier fixes how quickly the map escalates: Tier 1 (mission critical) hits
# Red readily; Tier 2 (important) is the same shape pushed one step right; Tier 3
# (not important) stays Green until the top-right corner.
MATERIALITY_ORDER = ("Low", "Medium", "High")
COMPLEXITY_ORDER = ("Low", "Medium", "High")
RISK_TIER_LABELS = TIER_LABELS  # tier == heatmap band (1/2/3)
RISK_HEATMAP_BY_TIER = {
    1: {  # Tier 1 — mission critical:  A R R / G A R / G G A
        ("High", "Low"): "Amber", ("High", "Medium"): "Red", ("High", "High"): "Red",
        ("Medium", "Low"): "Green", ("Medium", "Medium"): "Amber", ("Medium", "High"): "Red",
        ("Low", "Low"): "Green", ("Low", "Medium"): "Green", ("Low", "High"): "Amber",
    },
    2: {  # Tier 2 — important:  G A R / G G A / G G G
        ("High", "Low"): "Green", ("High", "Medium"): "Amber", ("High", "High"): "Red",
        ("Medium", "Low"): "Green", ("Medium", "Medium"): "Green", ("Medium", "High"): "Amber",
        ("Low", "Low"): "Green", ("Low", "Medium"): "Green", ("Low", "High"): "Green",
    },
    3: {  # Tier 3 — not important:  G G A / G G G / G G G
        ("High", "Low"): "Green", ("High", "Medium"): "Green", ("High", "High"): "Amber",
        ("Medium", "Low"): "Green", ("Medium", "Medium"): "Green", ("Medium", "High"): "Green",
        ("Low", "Low"): "Green", ("Low", "Medium"): "Green", ("Low", "High"): "Green",
    },
}
# Rolling window (days) for the "operational events past year" counter surfaced
# on the Risk Rating tab.
EVENTS_WINDOW_DAYS = 365

# Derived — keep validation and the UI in lockstep with the specs above.
EDITABLE_FIELDS = tuple(MODEL_FIELD_SPECS.keys())
FIELD_CHOICES = {
    key: spec["options"]
    for key, spec in MODEL_FIELD_SPECS.items()
    if spec["type"] == "choice"
}
