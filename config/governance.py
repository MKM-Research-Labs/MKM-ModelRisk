# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Model-governance domain vocabulary and field metadata (coding rule R1).

Generic and model-agnostic. ``MODEL_FIELD_SPECS`` is the single source of truth
for the inventory's scalar fields: each entry carries a label, an input type,
its group (for the grouped detail view), and — for choice fields — its options.
``EDITABLE_FIELDS`` and ``FIELD_CHOICES`` are derived from it so validation and
the UI never drift apart.

Structured collection fields (assumptions, limitations, validation questions,
remediation steps, change history, documents, model dependencies) are recorded
through their own commands and are intentionally not listed here.
"""

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
VALID_LIFECYCLE_STAGES = ("Development", "Validation", "Production", "Retired")
VALID_REVIEW_FREQUENCIES = ("Monthly", "Quarterly", "Semi-annual", "Annual")

TIER_MIN = 1
TIER_MAX = 5

# Fields captured on the registration form (besides the mandatory id + name).
REGISTER_FIELDS = (
    "company", "division", "department", "repo_location", "codebase",
    "category", "tier", "owner",
)

# Ordered scalar field specifications. type is one of: text | choice | date | tier.
MODEL_FIELD_SPECS = {
    # --- Organisation (company/division/department are backed by admin-managed
    #     reference lists; they render as dropdowns once the lists are populated) ---
    "company": {"label": "Company", "type": "text", "group": "Organisation", "reference": "company"},
    "division": {"label": "Division", "type": "text", "group": "Organisation", "reference": "division"},
    "department": {"label": "Department", "type": "text", "group": "Organisation", "reference": "department"},
    "repo_location": {"label": "Repository location", "type": "text", "group": "Organisation"},
    "codebase": {"label": "Codebase", "type": "text", "group": "Organisation"},
    # --- Classification ---
    "name": {"label": "Name", "type": "text", "group": "Classification"},
    "short_name": {"label": "Short name", "type": "text", "group": "Classification"},
    "description": {"label": "Description", "type": "text", "group": "Classification"},
    "category": {"label": "Category", "type": "text", "group": "Classification"},
    "tier": {"label": "Tier", "type": "tier", "group": "Classification"},
    "tier_rationale": {"label": "Tier rationale", "type": "text", "group": "Classification"},
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
    "model_owner_role": {"label": "Owner role", "type": "text", "group": "Governance"},
    "peer_reviewer": {
        "label": "Peer reviewer", "type": "text", "group": "Governance", "reference": "people",
    },
    "status": {"label": "Status", "type": "text", "group": "Governance"},
    "lifecycle_stage": {
        "label": "Lifecycle stage", "type": "choice",
        "options": VALID_LIFECYCLE_STAGES, "group": "Governance",
    },
    "version": {"label": "Version", "type": "text", "group": "Governance"},
    "validation_status": {
        "label": "Validation status", "type": "choice",
        "options": VALID_VALIDATION_STATUSES, "group": "Governance",
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
    "recertification_date": {"label": "Recertification", "type": "date", "group": "Review dates"},
    "validation_date": {"label": "Validation date", "type": "date", "group": "Review dates"},
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

# Human-readable tier descriptors (shown next to the tier badge).
TIER_LABELS = {1: "Maximum", 2: "Substantial", 3: "Moderate", 4: "Minimal", 5: "Negligible"}

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

# Overall risk-rating composite: (component key, label, weight). Weights sum to 1.
RISK_WEIGHTS = (
    ("validation_coverage", "Validation Coverage", 0.30),
    ("remediation_health", "Remediation Health", 0.25),
    ("review_currency", "Review Currency", 0.20),
    ("assumption_risk", "Assumption Risk", 0.15),
    ("limitation_risk", "Limitation Risk", 0.10),
)
RISK_ACCEPTABLE_AT = 0.75
RISK_CONDITIONAL_AT = 0.50

# Derived — keep validation and the UI in lockstep with the specs above.
EDITABLE_FIELDS = tuple(MODEL_FIELD_SPECS.keys())
FIELD_CHOICES = {
    key: spec["options"]
    for key, spec in MODEL_FIELD_SPECS.items()
    if spec["type"] == "choice"
}

# Closed value sets used by structured collections.
VALID_IMPACT = ("Low", "Medium", "High")
VALID_PRIORITY = ("Low", "Medium", "High")
VALID_REMEDIATION_STATUS = ("Open", "In Progress", "Closed")
VALID_VQ_STATUSES = (
    "Addressed", "Partially Addressed", "Not Addressed", "Not Applicable",
)
VALID_DEPENDENCY_DIRECTIONS = ("upstream", "downstream")

# Structured collections on a model: arrays of items. Each item is built from the
# field specs below; ``id_prefix`` seeds generated item ids (e.g. AS-001). One
# generic add/update/remove command set serves every collection.
COLLECTION_SPECS = {
    "assumptions": {"label": "Assumptions", "id_prefix": "AS", "fields": [
        {"key": "description", "label": "Description", "type": "text", "required": True},
        {"key": "impact", "label": "Impact", "type": "choice", "options": VALID_IMPACT},
        {"key": "monitoring", "label": "Monitoring", "type": "text"},
        {"key": "mitigation", "label": "Mitigation", "type": "text"},
    ]},
    "limitations": {"label": "Limitations", "id_prefix": "LM", "fields": [
        {"key": "description", "label": "Description", "type": "text", "required": True},
        {"key": "impact", "label": "Impact", "type": "choice", "options": VALID_IMPACT},
        {"key": "monitoring_trigger", "label": "Monitoring trigger", "type": "text"},
        {"key": "compensating_control", "label": "Compensating control", "type": "text"},
    ]},
    "validation_questions": {"label": "Validation questions", "id_prefix": "VQ", "fields": [
        {"key": "short_label", "label": "Topic", "type": "text"},
        {"key": "question", "label": "Question", "type": "text", "required": True},
        {"key": "status", "label": "Status", "type": "choice", "options": VALID_VQ_STATUSES},
        {"key": "evidence", "label": "Evidence", "type": "text"},
    ]},
    "version_history": {"label": "Versions", "id_prefix": "V", "fields": [
        {"key": "version", "label": "Version", "type": "text", "required": True},
        {"key": "date", "label": "Date", "type": "date"},
        {"key": "description", "label": "Description", "type": "text"},
        {"key": "author", "label": "Author", "type": "text"},
        {"key": "ref_document", "label": "Reference document", "type": "text"},
    ]},
    "remediation_steps": {"label": "Remediation", "id_prefix": "RM", "fields": [
        {"key": "description", "label": "Description", "type": "text", "required": True},
        {"key": "owner", "label": "Owner", "type": "text"},
        {"key": "priority", "label": "Priority", "type": "choice", "options": VALID_PRIORITY},
        {"key": "due_date", "label": "Due date", "type": "date"},
        {"key": "status", "label": "Status", "type": "choice", "options": VALID_REMEDIATION_STATUS},
    ]},
    "change_history": {"label": "Change history", "id_prefix": "CH", "fields": [
        {"key": "version", "label": "Version", "type": "text", "required": True},
        {"key": "date", "label": "Date", "type": "date"},
        {"key": "author", "label": "Author", "type": "text"},
        {"key": "change_type", "label": "Type", "type": "text"},
        {"key": "description", "label": "Description", "type": "text"},
    ]},
    "dependencies": {"label": "Model dependencies", "id_prefix": "DEP", "fields": [
        {"key": "direction", "label": "Direction", "type": "choice",
         "options": VALID_DEPENDENCY_DIRECTIONS, "required": True},
        {"key": "model_id", "label": "Related model", "type": "text", "required": True},
        {"key": "note", "label": "Note", "type": "text"},
    ]},
}

# --- Admin-managed reference data: people directory + menu lists ---
# Each spec's "display" field is the value shown in dropdowns that reference it.
REFERENCE_LISTS = ("people", "company", "division", "department")
REFERENCE_SPECS = {
    "people": {"label": "People", "id_prefix": "PE", "display": "name", "fields": [
        {"key": "name", "label": "Name", "type": "text", "required": True},
        {"key": "email", "label": "Email", "type": "text"},
        {"key": "role", "label": "Role", "type": "text"},
        {"key": "organisation", "label": "Organisation", "type": "text"},
    ]},
    "company": {"label": "Company", "id_prefix": "CO", "display": "value", "fields": [
        {"key": "value", "label": "Value", "type": "text", "required": True},
    ]},
    "division": {"label": "Division", "id_prefix": "DV", "display": "value", "fields": [
        {"key": "value", "label": "Value", "type": "text", "required": True},
    ]},
    "department": {"label": "Department", "id_prefix": "DP", "display": "value", "fields": [
        {"key": "value", "label": "Value", "type": "text", "required": True},
    ]},
}


# --- Model Risk Committee (MRC) meetings ---
VALID_MEETING_STATUSES = ("Scheduled", "In Progress", "Held", "Cancelled")
DEFAULT_MEETING_STATUS = "Scheduled"
VALID_ACTION_STATUSES = ("Open", "In Progress", "Closed")
VALID_ATTENDANCE = ("Present", "Apologies", "Absent")

# Scalar meeting fields (title/date are mandatory at scheduling time).
MEETING_FIELD_SPECS = {
    "title": {"label": "Title", "type": "text"},
    "date": {"label": "Date", "type": "date"},
    "time": {"label": "Time", "type": "text"},
    "location": {"label": "Location", "type": "text"},
    "chair": {"label": "Chair", "type": "text", "reference": "people"},
    "status": {"label": "Status", "type": "choice", "options": VALID_MEETING_STATUSES},
}
MEETING_FIELDS = tuple(MEETING_FIELD_SPECS.keys())

# Structured collections on a meeting — same generic engine as the inventory.
MRC_COLLECTION_SPECS = {
    "agenda": {"label": "Agenda", "id_prefix": "AG", "fields": [
        {"key": "title", "label": "Item", "type": "text", "required": True},
        {"key": "presenter", "label": "Presenter", "type": "text"},
    ]},
    "decisions": {"label": "Decisions", "id_prefix": "D", "fields": [
        {"key": "text", "label": "Decision", "type": "text", "required": True},
    ]},
    "actions": {"label": "Actions", "id_prefix": "A", "fields": [
        {"key": "description", "label": "Description", "type": "text", "required": True},
        {"key": "owner", "label": "Owner", "type": "text"},
        {"key": "due_date", "label": "Due date", "type": "date"},
        {"key": "status", "label": "Status", "type": "choice", "options": VALID_ACTION_STATUSES},
    ]},
    "participants": {"label": "Participants", "id_prefix": "P", "fields": [
        {"key": "name", "label": "Name", "type": "text", "required": True},
        {"key": "role", "label": "Role", "type": "text"},
        {"key": "organisation", "label": "Organisation", "type": "text"},
        {"key": "attendance", "label": "Attendance", "type": "choice", "options": VALID_ATTENDANCE},
    ]},
    "minutes": {"label": "Minutes", "id_prefix": "MIN", "fields": [
        {"key": "topic", "label": "Topic", "type": "text", "required": True},
        {"key": "note", "label": "Note", "type": "text"},
    ]},
    "models_in_scope": {"label": "Models in scope", "id_prefix": "MS", "fields": [
        {"key": "model_id", "label": "Model", "type": "text", "required": True},
        {"key": "note", "label": "Note", "type": "text"},
    ]},
}
