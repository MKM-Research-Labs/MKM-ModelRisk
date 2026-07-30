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
"""Product Valuation Model (Product) field metadata and vocabulary (coding rule R1)."""
from __future__ import annotations

from config.governance._collections import COLLECTION_SPECS
from config.governance._inventory import VALID_COMPLEXITY, VALID_MATERIALITY, VALID_RAG_RATINGS

VALID_PRODUCT_STATUS = ("Proposed", "Active", "Suspended", "Retired")

# The Calculating Agent is the one component that is not a model: it is the
# platform the product is priced on (QuantLib, an internal library), drawn from
# its own admin list. It stays a single binding, changed via rebind.
#
# The models a product pulls in are NOT fixed slots — see PRODUCT_COMPONENTS.
# A structured product combines several (a hazard curve, a recovery curve, a
# pricing engine) and how many is not knowable in advance, so three named
# columns could not describe one without inventing a slot for every shape.
PRODUCT_BINDINGS = ("calculating_agent",)

# The product's model components, held as a list. Each entry names what kind of
# component it is (from the admin model_type list, so a type added in Admin is
# immediately available as a component kind) and which inventory model fills it.
# Several components may share a type: two Curve Models is the ordinary case for
# structured credit, not an error.
PRODUCT_COMPONENTS = "components"

# Ordered scalar field specs. The calculating agent and the owner reference admin
# lists; the model components live in the ``components`` collection below.
PRODUCT_FIELD_SPECS = {
    "product": {"label": "Product", "type": "text", "group": "Product"},
    "product_id": {"label": "Product ID", "type": "text", "group": "Product"},
    "description": {"label": "Description", "type": "text", "group": "Product"},
    # --- Organisation (division / line of business backed by the admin-managed reference
    # lists, exactly like a model's org fields). A product may be allocated at
    # Division only — Line of Business is optional. These drive the product's
    # responsible MRC committee (matching_mrc on division / line of business).
    "division": {"label": "Division", "type": "text", "group": "Organisation", "reference": "division"},
    "line_of_business": {"label": "Line of Business", "type": "text", "group": "Organisation", "reference": "line_of_business"},
    # --- Classification (drives the risk-rating heatmap, identical to a model's:
    # tier band × Materiality × Complexity → RAG). Owner-set; the composite risk
    # rating and heatmap are computed from these plus the register collections.
    "tier": {"label": "Tier", "type": "tier", "group": "Classification"},
    "materiality": {"label": "Materiality", "type": "choice", "options": VALID_MATERIALITY,
                    "group": "Classification"},
    "complexity": {"label": "Complexity", "type": "choice", "options": VALID_COMPLEXITY,
                   "group": "Classification"},
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
    "product", "product_id", "description", "division", "line_of_business",
    "tier", "materiality", "complexity",
    "rag_rating", "status", "owner", "notes",
    "mrc_signoff_date", "mrc_signoff_meeting", "next_review_date", "last_review_date",
    "monitoring_approach", "monitoring_results",
)
PRODUCT_FIELD_CHOICES = {
    "status": VALID_PRODUCT_STATUS, "rag_rating": VALID_RAG_RATINGS,
    "materiality": VALID_MATERIALITY, "complexity": VALID_COMPLEXITY,
}

# The register form's minimum (besides the mandatory Product ID). Components are
# added on the product's own view rather than at registration: a product is often
# registered before it is known which models will fill it, and a form that demands
# them up front would be answered with placeholders. A product carrying no
# components is a completeness finding, which is where that gap belongs.
PRODUCT_REGISTER_FIELDS = ("product", "calculating_agent")

# Production-level registers — reuse the inventory's Limitations / Assumptions /
# Remediation shapes; Supporting Documentation reuses the per-aggregate Docs store.
PRODUCT_COLLECTION_SPECS = {
    # The models this product is built from. ``component_type`` is admin-managed
    # (the model_type list), so the vocabulary grows with the estate rather than
    # with a release; ``model_id`` resolves against the inventory, filtered to
    # models of that type.
    PRODUCT_COMPONENTS: {"label": "Components", "id_prefix": "CMP", "fields": [
        {"key": "component_type", "label": "Type", "type": "text",
         "reference": "model_type", "required": True},
        {"key": "model_id", "label": "Model", "type": "text",
         "reference": "model_inventory", "required": True},
        {"key": "role", "label": "Role in product", "type": "text"},
    ]},
    "limitations": COLLECTION_SPECS["limitations"],
    "assumptions": COLLECTION_SPECS["assumptions"],
    "remediation_steps": COLLECTION_SPECS["remediation_steps"],
    # SR 26-2 validation questions are a model-level concept and are not carried on
    # a Product: a Product validates through its component models, not a separate
    # product-level questionnaire. The operational-event log (impact) stays.
    "operational_failure_events": COLLECTION_SPECS["operational_failure_events"],
    # The RACI operating model — who is R/A/C/I for this product's use of models
    # in production. Defined at the product level (RACI folds into Product).
    "raci_roles": COLLECTION_SPECS["raci_roles"],
    # The MRC sign-off queue + history, shared shape with the model inventory.
    "signoff_requests": COLLECTION_SPECS["signoff_requests"],
    "signoff_history": COLLECTION_SPECS["signoff_history"],
    # Product-owned action items with an update history (same shape as a model's).
    "actions": COLLECTION_SPECS["actions"],
}
