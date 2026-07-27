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
"""Field and collection name maps from the PhysicalRisk source inventory to the
ModelRisk model schema, split from ``migrate_phys`` to keep it within the
file-size limit. Pure data: which source keys carry across and what they become."""
from __future__ import annotations

# Source scalar fields that map to a ModelRisk model field of the same key.
SCALAR_FIELDS = (
    "short_name", "description", "category", "tier", "materiality", "complexity",
    "tier_rationale", "methodology", "methodology_rationale", "source_module", "owner",
    "model_owner_role", "peer_reviewer", "status", "lifecycle_stage", "version",
    "validation_status", "rag_rating", "review_frequency", "last_review_date",
    "next_review_date", "mrc_signoff_date", "recertification_date", "validation_date",
)
# Source collection -> (ModelRisk collection, {source_key: modelrisk_key}).
COLLECTION_MAP = {
    "assumptions": ("assumptions",
                    {"description": "description", "impact": "impact",
                     "monitoring": "monitoring", "mitigation": "mitigation"}),
    "limitations": ("limitations",
                    {"description": "description", "impact": "impact",
                     "monitoring_trigger": "monitoring_trigger",
                     "compensating_control": "compensating_control"}),
    "remediation_steps": ("remediation_steps",
                          {"description": "description", "owner": "owner",
                           "priority": "priority", "due_date": "due_date", "status": "status"}),
    "version_history": ("version_history",
                        {"version": "version", "date": "date", "description": "description",
                         "author": "author", "document": "ref_document"}),
    "change_history": ("change_history",
                       {"version": "version", "date": "date", "author": "author",
                        "change_type": "change_type", "description": "description"}),
}
