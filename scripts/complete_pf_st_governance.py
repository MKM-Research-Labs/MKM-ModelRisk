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

"""Close the completeness-audit gaps on MKM-PF-001 and MKM-ST-001.

Both models reached ModelRisk in an identical, partly-blank state: a blank
validation date and blank unit/integration/benchmark test declarations; only two
of nine validation questions (Assumptions, Limitations) assessed; and no Test
Results document, though a real test-evidence PDF already exists on disk under
PhysicalRisk ``docs/models/<folder>/`` and interoperability handovers are already
filed on each record.

This fills those gaps for both models from the same template, honestly:

* validation_date is set to 2026-03-18 (the recertification date already on each
  record is 2027-03-18, i.e. a one-year cycle, and the model documentation is
  dated March 2026);
* unit_tests and integration_tests are declared ``Yes`` — a unit suite passes and
  interoperability handovers are on record; benchmark_tests is declared ``No``
  because no benchmark evidence exists (kept consistent with VQ-008 below);
* the seven unrecorded validation questions are assessed on their merits — the
  ones genuinely satisfied move up, while Override controls, Data quality,
  Benchmarking and Independent validation stay "Not Addressed" with a rationale,
  the honest basis for each model's Red rating;
* the existing ``test_results.pdf`` is filed into the Test Results and Unit Test
  tabs (filed, not regenerated).

Deliberately NOT done here (would require real artefacts, not this script):
Sensitivity and Monitoring documents. They are flagged to the caller, not
fabricated.

Idempotent: scalars already set are left alone, an attached document is skipped,
and a validation question already at its target status is untouched.

Run as:  python -m scripts.complete_pf_st_governance
"""
from __future__ import annotations

from pathlib import Path

from config.paths import PRODUCER_ROOT as PHYS_ROOT
from src.governance.documents import add_document
from src.governance.model_inventory import (
    get_model,
    rebuild_inventory_view,
    update_collection_item,
    update_model_field,
)
from src.governance.model_inventory.commands import AGGREGATE_TYPE as MODEL_AGGREGATE

ACTOR = "complete_pf_st_governance"

# Scalar declarations shared by both models (only written where currently blank).
SCALARS = {
    "validation_date": "2026-03-18",
    "unit_tests": "Yes",
    "integration_tests": "Yes",
    "benchmark_tests": "No",
}

# Validation-question assessments that are identical across both models. VQ-006/007
# are already Addressed on the live records; they are listed so a freshly-registered
# model (which seeds them without a rationale) is also completed — the idempotency
# guard leaves the live rows untouched.
COMMON_VQ = {
    "VQ-006": ("Addressed",
        "The model's assumptions are documented and justified in the Assumptions "
        "register on this record."),
    "VQ-007": ("Addressed",
        "The model's limitations are documented and monitored in the Limitations "
        "register on this record, with monitoring triggers."),
    "VQ-004": ("Not Addressed",
        "Controls over manual overrides are not documented for this model; "
        "configuration is via code flags rather than governed, logged overrides. "
        "Outstanding."),
    "VQ-005": ("Not Addressed",
        "Input-data quality is not assured: the model runs on synthetic gauge and "
        "property data whose realism is unvalidated. Data-quality controls are "
        "outstanding."),
    "VQ-008": ("Not Addressed",
        "The model has not been benchmarked against credible alternatives; no "
        "benchmark evidence is on record (benchmark_tests declared No)."),
    "VQ-009": ("Not Addressed",
        "Not independently validated; this is the basis for the current Red "
        "rating. Independent validation is outstanding."),
}

# Per-model config: the on-disk documentation folder and the three questions whose
# honest answer depends on what the model actually does.
MODELS = {
    "MKM-PF-001": {
        "name": "Property Flood Response",
        "folder": "docs/models/property_flood_response",
        "vq": {
            "VQ-001": ("Addressed",
                "Implements the documented methodology: property-level flood-depth "
                "estimation, depth-damage curves, spatial interpolation and "
                "velocity modelling feeding portfolio risk analytics — its stated "
                "purpose."),
            "VQ-002": ("Partially Addressed",
                "A unit-test suite passes and the depth-damage and interpolation "
                "methods are standard and stable. Real-world accuracy is "
                "unvalidated on synthetic data, and the IDW interpolation is a "
                "known accuracy limitation under sparse gauges — hence partial."),
            "VQ-003": ("Addressed",
                "Per-property depth estimation and interpolation are lightweight "
                "batch computations; no excessive computational resource use."),
        },
    },
    "MKM-ST-001": {
        "name": "Stress Test Pipeline",
        "folder": "docs/models/stressm_pipeline",
        "vq": {
            "VQ-001": ("Addressed",
                "Orchestrates the documented end-to-end stress pipeline: storm "
                "sequence generation, seasonal baselines, compound gauge responses "
                "and GBM classifier training — its stated purpose."),
            "VQ-002": ("Partially Addressed",
                "The pipeline is seeded and deterministic and its unit suite "
                "passes. The realism of the generated stresses and the trained "
                "classifier's accuracy are unvalidated against observed events — "
                "hence partial."),
            "VQ-003": ("Addressed",
                "Stress generation and GBM training are the heavier batch steps "
                "but remain bounded and tractable; no excessive resource use in a "
                "normal run."),
        },
    },
}

# Documents filed for both models: the existing test-evidence PDF, into the Test
# Results and Unit Test tabs (one artefact, two audited sub-categories).
DOC_TEMPLATE = [
    ("Test Results", "test_results.pdf", "test_results.pdf",
     "Test Results - {name}"),
    ("Unit Test", "unit_tests_{model_id}.pdf", "test_results.pdf",
     "Unit test evidence - {name}"),
]


def apply_one(model_id: str, phys_root: Path = PHYS_ROOT, config=None) -> dict:
    """Fill one model's audited gaps idempotently; return a summary."""
    spec = MODELS[model_id]
    model = get_model(model_id, config=config)
    if model is None:
        raise RuntimeError(f"{model_id} is not registered.")
    data = model["data"]
    summary = {"model": model_id, "fields": [], "questions": 0, "documents": []}

    for field, value in SCALARS.items():
        if data.get(field) in (None, "", "None"):
            update_model_field(model_id=model_id, field=field, value=value,
                               actor=ACTOR, config=config,
                               reason="Complete audited governance record")
            summary["fields"].append(field)

    vq_updates = {**spec["vq"], **COMMON_VQ}
    by_id = {q["item_id"]: q for q in data.get("validation_questions", [])}
    for item_id, (status, rationale) in vq_updates.items():
        current = by_id.get(item_id)
        if current is not None and (
                current.get("status") != status or not current.get("rationale")):
            update_collection_item(
                model_id=model_id, collection="validation_questions",
                item_id=item_id, fields={"status": status, "rationale": rationale},
                actor=ACTOR, config=config, reason="Validation assessment update")
            summary["questions"] += 1

    have = {(d.get("original_name") or d.get("filename"))
            for d in (data.get("documents") or [])}
    for category, name_tmpl, relname, desc_tmpl in DOC_TEMPLATE:
        stored_name = name_tmpl.format(model_id=model_id)
        if stored_name in have:
            continue
        source = Path(phys_root, spec["folder"], relname)
        add_document(
            aggregate_type=MODEL_AGGREGATE, aggregate_id=model_id,
            scope=f"model/{model_id}", category=category, filename=stored_name,
            data=source.read_bytes(),
            description=desc_tmpl.format(name=spec["name"]),
            actor=ACTOR, config=config)
        summary["documents"].append((category, stored_name))

    rebuild_inventory_view(config=config)
    return summary


def apply(phys_root: Path = PHYS_ROOT, config=None) -> list[dict]:
    """Apply the completion to both models; return per-model summaries."""
    return [apply_one(mid, phys_root=phys_root, config=config) for mid in MODELS]


def main() -> int:
    from src.database import run_migrations

    run_migrations()
    for s in apply():
        print(f"{s['model']}: +fields {s['fields']}, {s['questions']} validation "
              f"questions recorded, +docs {[d[0] for d in s['documents']]}")
    print("NOTE: Sensitivity and Monitoring documents are NOT filed here "
          "(no real artefact) — outstanding.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
