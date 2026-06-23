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
"""Model-inventory scalar fields and risk vocabulary (coding rule R1).

``MODEL_FIELD_SPECS`` is the single source of truth for the inventory's scalar
fields: each entry carries a label, an input type, its group (for the grouped
detail view), and — for choice fields — its options. ``EDITABLE_FIELDS`` and
``FIELD_CHOICES`` are derived from it so validation and the UI never drift apart.
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
# Company is NOT here — it comes from the org-scope selector in the header, so a
# model is defined by its ID within the selected Company. Division and Department
# are captured on the form.
REGISTER_FIELDS = (
    "division", "department", "repo_location", "codebase", "category", "tier", "owner",
)

# Ordered scalar field specifications. type is one of: text | choice | date | tier.
MODEL_FIELD_SPECS = {
    # --- Organisation (company/division/department are backed by admin-managed
    #     reference lists; company is set via the header org-scope selector) ---
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
