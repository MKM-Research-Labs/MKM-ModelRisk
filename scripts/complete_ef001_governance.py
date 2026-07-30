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

"""Close the record-level governance gaps a completeness audit found on MKM-EF-001.

EF-001 was registered outside the bulk migration, so it reached ModelRisk with a
blank description and validation/recertification dates, no version or change
history, and validation questions that were recorded but under-assessed. This
fills those in — with true, evidence-backed content, never inflated: the
benchmark and independent-validation questions stay "Not Addressed" because
neither has been done, and data quality stays honest about the unvalidated
lambda.

Missing document evidence (Test Results, Unit Test, Analysis, Integration Test)
is handled separately by ``scripts.attach_ef001_docs`` / generation, not here.

Idempotent: a scalar already set is left alone, a history entry already present
is skipped, and a validation question already at its target status is untouched.

Run as:  python -m scripts.complete_ef001_governance
"""
from __future__ import annotations

from src.governance.model_inventory import (
    add_collection_item,
    get_model,
    rebuild_inventory_view,
    update_collection_item,
    update_model_field,
)

ACTOR = "complete_ef001_governance"
MODEL_ID = "MKM-EF-001"

# --- Scalar fields (only written if currently blank) ------------------------
DESCRIPTION = (
    "The Event Frequency Model supplies the time dimension the flood chain "
    "lacks: it estimates the per-year arrival rate (lambda) of qualifying storm "
    "events on a catchment and annualises the per-event flood conditional as "
    "1 - exp(-lambda*p), turning the platform's per-storm flood probabilities "
    "into per-year PRS spreads. Peaks-over-threshold extraction with runs-method "
    "declustering; Poisson/Negative-Binomial family selection by a small-sample "
    "dispersion test; a Monte Carlo year simulation reconciled to its exact "
    "closed form. Sits downstream of the GEV hazard curve (MKM-GH-001) and "
    "upstream of PRS pricing (MKM-PR-001)."
)
# The first-line validation assessment was recorded at the Q4 review; independent
# validation (VQ-009) is separate and remains outstanding.
VALIDATION_DATE = "2026-07-29"
# Annual recertification, aligned with the Annual review frequency.
RECERTIFICATION_DATE = "2027-07-29"

SCALARS = {
    "description": DESCRIPTION,
    "validation_date": VALIDATION_DATE,
    "recertification_date": RECERTIFICATION_DATE,
}

# --- Version history (real milestones) --------------------------------------
VERSIONS = [
    {"version": "0.1.0", "date": "2026-07-22", "author": "David K Kelly",
     "lifecycle": "New",
     "description": "Stage 1 — peaks-over-threshold extraction with runs-method "
                    "declustering, arrival-rate estimation and provenance."},
    {"version": "1.0.0", "date": "2026-07-26", "author": "David K Kelly",
     "lifecycle": "Being Enhanced",
     "description": "Release — Poisson/Negative-Binomial family selection "
                    "(Stage 2), wired into gauge/property/commercial pricing "
                    "(Stages 3-4), governance registration (Stage 5)."},
    {"version": "1.1.0", "date": "2026-07-28", "author": "David K Kelly",
     "lifecycle": "Being Enhanced",
     "description": "Track B — loss YLT/ELT and monetary uplift, non-stationary "
                    "term structure, decoupled-wind seam and the sensitivity "
                    "harness; all behaviour-preserving by default."},
]

# --- Change history ---------------------------------------------------------
CHANGES = [
    {"version": "1.0.0", "date": "2026-07-26", "author": "David K Kelly",
     "description": "Frequency layer wired into the hazard builder and the "
                    "property/commercial pricing legs; the legacy "
                    "flood_count/num_storms metric retained for parallel run."},
    {"version": "1.1.0", "date": "2026-07-28", "author": "David K Kelly",
     "description": "Additive loss view, non-stationary term structure and "
                    "decoupled-wind seam added off by default; one-off lambda "
                    "sensitivity analysis produced."},
]

# --- Validation questions: honest status upgrades where evidence now exists --
# (item_id -> (status, rationale)). Only questions whose assessment has moved are
# listed; VQ-005/008/009 stay Not Addressed because data quality, benchmarking
# and independent validation genuinely are not done.
VQ_UPDATES = {
    "VQ-002": ("Partially Addressed",
        "Numerical accuracy and stability are demonstrated: the Monte Carlo "
        "reconciles to its exact closed form within sampling error (a verified "
        "z-score gate), runs are seeded and reproducible, and the unit-test "
        "suite passes with the loss/sensitivity modules at full coverage. "
        "Real-world accuracy still depends on the unvalidated lambda, and "
        "back-testing is outstanding, so this is partial, not full."),
    "VQ-003": ("Addressed",
        "Resource use is bounded by design: the year simulation resamples a "
        "pre-computed catalogue rather than regenerating the hydrology, so a "
        "full-portfolio ten-thousand-year run costs about 0.4s. No excessive "
        "resource use in the overnight batch."),
    "VQ-004": ("Addressed",
        "Every model parameter lives in the config.frequency package (house "
        "rule R1) with no per-run manual overrides; the only override — the "
        "distribution-family force — is logged with its justification (SR 11-7). "
        "The controls over overrides are therefore documented and enforced."),
}


def apply(config=None) -> dict:
    """Fill the audited record gaps idempotently; return a summary."""
    model = get_model(MODEL_ID, config=config)
    if model is None:
        raise RuntimeError(f"{MODEL_ID} is not registered.")
    data = model["data"]
    summary = {"fields": [], "versions": 0, "changes": 0, "questions": 0}

    for field, value in SCALARS.items():
        current = data.get(field)
        if current in (None, "", "None"):
            update_model_field(model_id=MODEL_ID, field=field, value=value,
                               actor=ACTOR, config=config,
                               reason="Complete audited governance record")
            summary["fields"].append(field)

    have_versions = {v.get("version") for v in data.get("version_history", [])}
    for entry in VERSIONS:
        if entry["version"] not in have_versions:
            add_collection_item(model_id=MODEL_ID, collection="version_history",
                                fields=entry, actor=ACTOR, config=config)
            summary["versions"] += 1

    have_changes = {(c.get("version"), c.get("description"))
                    for c in data.get("change_history", [])}
    for entry in CHANGES:
        if (entry["version"], entry["description"]) not in have_changes:
            add_collection_item(model_id=MODEL_ID, collection="change_history",
                                fields=entry, actor=ACTOR, config=config)
            summary["changes"] += 1

    by_id = {q["item_id"]: q for q in data.get("validation_questions", [])}
    for item_id, (status, rationale) in VQ_UPDATES.items():
        current = by_id.get(item_id)
        if current is not None and current.get("status") != status:
            update_collection_item(
                model_id=MODEL_ID, collection="validation_questions",
                item_id=item_id, fields={"status": status, "rationale": rationale},
                actor=ACTOR, config=config, reason="Validation assessment update")
            summary["questions"] += 1

    rebuild_inventory_view(config=config)
    return summary


def main() -> int:
    from src.database import run_migrations

    run_migrations()
    s = apply()
    print(f"EF-001 record: +fields {s['fields']}, +{s['versions']} versions, "
          f"+{s['changes']} changes, {s['questions']} validation questions updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
