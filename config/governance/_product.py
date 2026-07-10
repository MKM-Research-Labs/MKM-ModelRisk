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
"""Product Valuation Model (Product) field metadata and vocabulary (coding rule R1)."""
from __future__ import annotations

from config.governance._collections import COLLECTION_SPECS
from config.governance._inventory import VALID_COMPLEXITY, VALID_MATERIALITY, VALID_RAG_RATINGS

VALID_PRODUCT_STATUS = ("Proposed", "Active", "Suspended", "Retired")

# The three component bindings: set at registration, changed only via a rebind.
# The derived identifier reads them in this order (Analytics leads — it is the
# engine that prices the product; then Market Data, then the Calculating Agent).
PRODUCT_BINDINGS = ("analytics_model", "market_data_model", "calculating_agent")

# Ordered scalar field specs. ``analytics_model`` and ``market_data_model`` both
# reference the Model Inventory (resolved specially, not via a reference list —
# a Market Data Model is an inventory model of type "Market Data Model"); the
# calculating agent and the owner reference admin lists.
PRODUCT_FIELD_SPECS = {
    "product": {"label": "Product", "type": "text", "group": "Product"},
    "product_id": {"label": "Product ID", "type": "text", "group": "Product"},
    "description": {"label": "Description", "type": "text", "group": "Product"},
    # --- Organisation (division/department backed by the admin-managed reference
    # lists, exactly like a model's org fields). A product may be allocated at
    # Division only — Department is optional. These drive the product's
    # responsible MRC committee (matching_mrc on division/department).
    "division": {"label": "Division", "type": "text", "group": "Organisation", "reference": "division"},
    "department": {"label": "Department", "type": "text", "group": "Organisation", "reference": "department"},
    # --- Classification (drives the risk-rating heatmap, identical to a model's:
    # tier band × Materiality × Complexity → RAG). Owner-set; the composite risk
    # rating and heatmap are computed from these plus the register collections.
    "tier": {"label": "Tier", "type": "tier", "group": "Classification"},
    "materiality": {"label": "Materiality", "type": "choice", "options": VALID_MATERIALITY,
                    "group": "Classification"},
    "complexity": {"label": "Complexity", "type": "choice", "options": VALID_COMPLEXITY,
                   "group": "Classification"},
    "analytics_model": {"label": "Analytics Model", "type": "text", "group": "Bindings"},
    "market_data_model": {"label": "Market Data Model", "type": "text", "group": "Bindings"},
    "calculating_agent": {"label": "Calculating Agent", "type": "text", "group": "Bindings",
                          "reference": "calculating_agent"},
    "rag_rating": {"label": "RAG rating", "type": "choice", "options": VALID_RAG_RATINGS,
                   "group": "Risk rating"},
    "status": {"label": "Status", "type": "choice", "options": VALID_PRODUCT_STATUS, "group": "Governance"},
    "owner": {"label": "Owner", "type": "text", "group": "Governance", "reference": "people"},
    "notes": {"label": "Notes", "type": "text", "group": "Governance"},
    "mrc_signoff_date": {"label": "MRC sign-off", "type": "date", "group": "Review dates"},
    # The meeting that granted the sign-off — displayed as the MRC sign-off value.
    "mrc_signoff_meeting": {"label": "MRC sign-off meeting", "type": "text", "group": "Review dates"},
    "next_review_date": {"label": "Next review", "type": "date", "group": "Review dates"},
    "last_review_date": {"label": "Last review", "type": "date", "group": "Review dates"},
    "monitoring_approach": {"label": "Monitoring approach", "type": "text", "group": "Monitoring"},
    "monitoring_results": {"label": "Monitoring results", "type": "text", "group": "Monitoring"},
}

# Fields editable through the generic field-edit command (the bindings are not —
# they are changed via rebind; ``status`` Retired is reached via retire).
PRODUCT_EDITABLE_FIELDS = (
    "product", "product_id", "description", "division", "department",
    "tier", "materiality", "complexity",
    "rag_rating", "status", "owner", "notes",
    "mrc_signoff_date", "mrc_signoff_meeting", "next_review_date", "last_review_date",
    "monitoring_approach", "monitoring_results",
)
PRODUCT_FIELD_CHOICES = {
    "status": VALID_PRODUCT_STATUS, "rag_rating": VALID_RAG_RATINGS,
    "materiality": VALID_MATERIALITY, "complexity": VALID_COMPLEXITY,
}

# The register form's minimum (besides the mandatory Product ID).
PRODUCT_REGISTER_FIELDS = ("product", "analytics_model", "market_data_model", "calculating_agent")

# Production-level registers — reuse the inventory's Limitations / Assumptions /
# Remediation shapes; Supporting Documentation reuses the per-aggregate Docs store.
PRODUCT_COLLECTION_SPECS = {
    "limitations": COLLECTION_SPECS["limitations"],
    "assumptions": COLLECTION_SPECS["assumptions"],
    "remediation_steps": COLLECTION_SPECS["remediation_steps"],
    # Composite risk-rating inputs, shared shape with the model inventory: the
    # validation-question tracker (coverage) and the operational-event log
    # (impact). Give the product the same risk assessment as a model.
    "validation_questions": COLLECTION_SPECS["validation_questions"],
    "operational_failure_events": COLLECTION_SPECS["operational_failure_events"],
    # The MRC sign-off queue + history, shared shape with the model inventory.
    "rag_signoff_requests": COLLECTION_SPECS["rag_signoff_requests"],
    "rag_signoff_history": COLLECTION_SPECS["rag_signoff_history"],
}
