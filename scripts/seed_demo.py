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
"""Seed the inventory with a few example models. Run: ``python scripts/seed_demo.py``."""
from __future__ import annotations

from src.database import run_migrations
from src.governance.errors import DomainError
from src.governance.model_inventory import (
    add_collection_item,
    register_model,
    rebuild_inventory_view,
    update_model_field,
)

MODELS = [
    {
        "id": "MKM-GH-001", "name": "GEV Hazard Curve Model",
        "fields": {"category": "Hazard", "tier": 1, "owner": "David K Kelly",
                   "model_owner_role": "Chief Science Officer", "rag_rating": "Green",
                   "lifecycle_stage": "Production", "materiality": "High", "complexity": "High",
                   "version": "1.0.0", "next_review_date": "2026-04-15",
                   "description": "Generalised Extreme Value hazard curve for storm severity.",
                   "methodology": "Block-maxima GEV fit with L-moments estimation."},
        "assumptions": [{"description": "Annual maxima are GEV-distributed", "impact": "High"}],
        "limitations": [{"description": "Short observational record", "impact": "Medium"}],
    },
    {
        "id": "MKM-SI-001", "name": "Storm Intensity Distribution",
        "fields": {"category": "Hazard", "tier": 2, "owner": "David K Kelly",
                   "model_owner_role": "Chief Science Officer", "rag_rating": "Amber",
                   "lifecycle_stage": "Development", "materiality": "Medium", "complexity": "Medium",
                   "version": "1.0.0", "next_review_date": "2026-06-15",
                   "description": "Hybrid Normal-Pareto distribution for storm rainfall intensity.",
                   "methodology": "Hybrid Normal-GPD with MLE threshold estimation."},
        "assumptions": [{"description": "Storm events are independent", "impact": "Medium"}],
        "limitations": [{"description": "No spatial correlation modelled", "impact": "High"}],
    },
    {
        "id": "MKM-PR-001", "name": "PRS Pricing Model",
        "fields": {"category": "Pricing", "tier": 1, "owner": "David K Kelly",
                   "model_owner_role": "Chief Science Officer", "rag_rating": "Green",
                   "lifecycle_stage": "Production", "materiality": "High", "complexity": "High",
                   "version": "2.1.0", "next_review_date": "2026-03-01",
                   "description": "Physical Risk Swap pricing engine.",
                   "methodology": "Monte Carlo simulation over coupled hazard scenarios."},
        "assumptions": [{"description": "Risk-neutral pricing applies", "impact": "High"}],
    },
    {
        "id": "MKM-DD-001", "name": "Depth-Damage Model",
        "fields": {"category": "Loss", "tier": 2, "owner": "A. Singh",
                   "model_owner_role": "Lead Quant", "rag_rating": "Amber",
                   "lifecycle_stage": "Validation", "materiality": "Medium", "complexity": "Medium",
                   "version": "0.9.0", "next_review_date": "2026-08-01",
                   "description": "Flood depth to property damage relationship.",
                   "methodology": "Calibrated depth-damage curves by property archetype."},
        "limitations": [{"description": "Calibrated on residential only", "impact": "Medium"}],
    },
    {
        "id": "MKM-PV-001", "name": "Property Valuation Model",
        "fields": {"category": "Valuation", "tier": 3, "owner": "A. Singh",
                   "model_owner_role": "Lead Quant", "rag_rating": "Green",
                   "lifecycle_stage": "Production", "materiality": "Low", "complexity": "Low",
                   "version": "1.4.0", "next_review_date": "2027-01-10",
                   "description": "Automated valuation model for residential property.",
                   "methodology": "Hedonic regression with locality adjustments."},
    },
]


def seed() -> int:
    run_migrations()
    created = 0
    for model in MODELS:
        try:
            register_model(model_id=model["id"], name=model["name"], actor="seed-script",
                           fields=model["fields"], reason="Demo seed")
            created += 1
        except DomainError:
            continue  # already registered
        for collection in ("assumptions", "limitations"):
            for fields in model.get(collection, []):
                add_collection_item(model_id=model["id"], collection=collection,
                                    fields=fields, actor="seed-script", reason="Demo seed")
    rebuild_inventory_view()
    return created


if __name__ == "__main__":
    count = seed()
    print(f"Seeded {count} new model(s); inventory rebuilt.")
