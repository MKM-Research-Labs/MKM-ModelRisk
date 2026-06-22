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
    # --- Organisation ---
    "company": {"label": "Company", "type": "text", "group": "Organisation"},
    "division": {"label": "Division", "type": "text", "group": "Organisation"},
    "department": {"label": "Department", "type": "text", "group": "Organisation"},
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
    "owner": {"label": "Owner", "type": "text", "group": "Governance"},
    "model_owner_role": {"label": "Owner role", "type": "text", "group": "Governance"},
    "peer_reviewer": {"label": "Peer reviewer", "type": "text", "group": "Governance"},
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
}

# Derived — keep validation and the UI in lockstep with the specs above.
EDITABLE_FIELDS = tuple(MODEL_FIELD_SPECS.keys())
FIELD_CHOICES = {
    key: spec["options"]
    for key, spec in MODEL_FIELD_SPECS.items()
    if spec["type"] == "choice"
}

# --- Model Risk Committee (MRC) meetings ---
MEETING_FIELDS = ("title", "date", "time", "location", "chair", "status")
VALID_MEETING_STATUSES = ("Scheduled", "In Progress", "Held", "Cancelled")
DEFAULT_MEETING_STATUS = "Scheduled"
VALID_ACTION_STATUSES = ("Open", "In Progress", "Closed")
DEFAULT_ACTION_STATUS = "Open"
