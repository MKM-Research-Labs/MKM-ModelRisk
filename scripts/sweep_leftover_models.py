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

"""Complete the three models left out of the Test Results backlog: WD, WS, BRF.

These three already carried a Test Results document (so they were not in the
17-model backlog), but never received the rest of the governance completion. This
finishes them, honestly and idempotently: files a Unit Test document from the
existing on-disk test evidence, sets the test declarations and dates, and records
the validation questions.

Two of them (WD, WS) take the standard flood/wind-chain assessment (4 Addressed /
1 Partial / 4 Not Addressed). BRF-001 is deliberately different: it is a single
deterministic, bounded transform (a BRI flood score to a floor-level uplift) with
no input data or overrides of its own, so several questions are honestly *Not
Applicable* rather than Not Addressed. Its existing status set is preserved — only
the missing rationales are filled — so the sweep does not downgrade a legitimate
Not Applicable to Not Addressed.

Idempotent: scalars already set are left alone, an attached document is skipped,
and a validation question already at its target status with a rationale is
untouched.

Run as:  python -m scripts.sweep_leftover_models
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

ACTOR = "sweep_leftover_models"

_A_ASSUMPTIONS = ("Addressed",
    "The model's assumptions are documented and justified in the Assumptions "
    "register on this record.")
_A_LIMITATIONS = ("Addressed",
    "The model's limitations are documented and monitored in the Limitations "
    "register on this record, with monitoring triggers.")
_NA_OVERRIDES = ("Not Addressed",
    "Controls over manual overrides are not documented; parameters live in the "
    "config package but there is no governed, logged override mechanism. "
    "Outstanding.")
_NA_DATA = ("Not Addressed",
    "Input-data quality is not assured: the model runs on synthetic data whose "
    "realism is unvalidated. Data-quality controls are outstanding.")
_NA_BENCHMARK = ("Not Addressed",
    "The model has not been benchmarked against a credible independent "
    "alternative; no benchmark evidence is on record (benchmark_tests = No).")
_NA_INDEP = ("Not Addressed",
    "Not independently validated; this is the basis for the current Red rating. "
    "Independent validation is outstanding.")


def _standard_vq(ronseal, accuracy, resource):
    return {
        "VQ-001": ("Addressed", ronseal),
        "VQ-002": ("Partially Addressed", accuracy),
        "VQ-003": ("Addressed", resource),
        "VQ-004": _NA_OVERRIDES,
        "VQ-005": _NA_DATA,
        "VQ-006": _A_ASSUMPTIONS,
        "VQ-007": _A_LIMITATIONS,
        "VQ-008": _NA_BENCHMARK,
        "VQ-009": _NA_INDEP,
    }


MODELS = {
    "MKM-WD-001": {
        "name": "Wind Damage",
        "folder": "wind_damage",
        "validation_date": "2026-06-17",
        "recertification_date": "2027-06-17",
        "vq": _standard_vq(
            "Computes a per-property wind-damage ratio from peak sustained wind "
            "during a typhoon event via a saturated sigmoid about a BRI-adjusted "
            "50%-damage threshold (v_50), mirroring the flood-damage architecture "
            "— its documented purpose.",
            "The sigmoid is calibrated and stable and the unit suite passes; the "
            "vulnerability curve is not validated against observed wind-loss data "
            "and it consumes the unvalidated MKM-TC-001 wind field, so this is "
            "partial.",
            "A closed-form per-property sigmoid evaluation; negligible "
            "computational resource use."),
    },
    "MKM-WS-001": {
        "name": "Event Wind Lookup",
        "folder": "wind_speed",
        "validation_date": "2026-05-27",
        "recertification_date": "2027-05-27",
        "vq": _standard_vq(
            "Returns the per-point sustained wind for a stored typhoon trajectory "
            "at a given hour and location by evaluating the MKM-TC-001 wind field "
            "— its documented purpose.",
            "The lookup is deterministic with a passing unit suite; its accuracy "
            "is that of the underlying TC-001 wind field, which is unvalidated on "
            "synthetic tracks, so this is partial.",
            "A per-point field evaluation; negligible computational resource use."),
    },
    # BRF-001: a deterministic bounded transform. Its existing status set (several
    # Not Applicable) is preserved; only the missing rationales are supplied.
    "MKM-BRF-001": {
        "name": "BRI-Adjusted Floor Level Model",
        "folder": "bri_floor",
        "validation_date": "2026-06-02",
        "vq": {
            "VQ-001": ("Addressed",
                "Implements a continuous monotone ramp translating the "
                "BRIFloodScore into an additive floor-level uplift that raises the "
                "effective flood threshold — its documented purpose."),
            "VQ-002": ("Addressed",
                "A closed-form, deterministic and bounded transform (the uplift is "
                "clamped to a documented maximum); the unit suite passes and "
                "results are exactly reproducible, so accuracy and stability are "
                "demonstrated for what the function computes."),
            "VQ-003": ("Addressed",
                "A scalar arithmetic evaluation per property; negligible "
                "computational resource use."),
            "VQ-004": ("Not Applicable",
                "The model has no manual overrides — it is a fixed deterministic "
                "formula whose only parameters live in the config package — so "
                "override controls do not apply."),
            "VQ-005": ("Not Applicable",
                "The model consumes a single BRIFloodScore already governed by "
                "MKM-BRI-001 and introduces no input data of its own, so a "
                "separate data-quality assessment does not apply."),
            "VQ-006": _A_ASSUMPTIONS,
            "VQ-007": _A_LIMITATIONS,
            "VQ-008": ("Not Applicable",
                "A deterministic resilience-credit transform has no distributional "
                "output to benchmark against a credible alternative; benchmarking "
                "does not apply."),
            "VQ-009": ("Not Addressed",
                "The uplift ramp's anchor points are expert-judgement calibrations "
                "that have not been independently validated; independent "
                "validation is outstanding."),
        },
    },
}


def apply_one(model_id: str, phys_root: Path = PHYS_ROOT, config=None) -> dict:
    """Complete one leftover model idempotently; return a summary."""
    spec = MODELS[model_id]
    model = get_model(model_id, config=config)
    if model is None:
        raise RuntimeError(f"{model_id} is not registered.")
    data = model["data"]
    summary = {"model": model_id, "fields": [], "questions": 0, "documents": []}

    scalars = {
        "unit_tests": "Yes",
        "integration_tests": "Yes",
        "benchmark_tests": "No",
        "validation_date": spec["validation_date"],
    }
    if "recertification_date" in spec:
        scalars["recertification_date"] = spec["recertification_date"]
    for field, value in scalars.items():
        if data.get(field) in (None, "", "None"):
            update_model_field(model_id=model_id, field=field, value=value,
                               actor=ACTOR, config=config,
                               reason="Complete audited governance record (leftover sweep)")
            summary["fields"].append(field)

    by_id = {q["item_id"]: q for q in data.get("validation_questions", [])}
    for item_id, (status, rationale) in spec["vq"].items():
        current = by_id.get(item_id)
        if current is not None and (
                current.get("status") != status or not current.get("rationale")):
            update_collection_item(
                model_id=model_id, collection="validation_questions",
                item_id=item_id, fields={"status": status, "rationale": rationale},
                actor=ACTOR, config=config, reason="Validation assessment update")
            summary["questions"] += 1

    source = Path(phys_root, "docs", "models", spec["folder"], "test_results.pdf")
    have = {(d.get("original_name") or d.get("filename"))
            for d in (data.get("documents") or [])}
    stored_name = f"unit_tests_{model_id}.pdf"
    if stored_name not in have:
        add_document(
            aggregate_type=MODEL_AGGREGATE, aggregate_id=model_id,
            scope=f"model/{model_id}", category="Unit Test", filename=stored_name,
            data=source.read_bytes(),
            description=f"Unit test evidence - {spec['name']}",
            actor=ACTOR, config=config)
        summary["documents"].append(("Unit Test", stored_name))

    rebuild_inventory_view(config=config)
    return summary


def apply(phys_root: Path = PHYS_ROOT, config=None) -> list[dict]:
    """Complete all three leftover models; return per-model summaries."""
    return [apply_one(mid, phys_root=phys_root, config=config) for mid in MODELS]


def main() -> int:
    from src.database import run_migrations

    run_migrations()
    for s in apply():
        print(f"{s['model']}: +fields {s['fields']}, {s['questions']} validation "
              f"questions recorded, +docs {[d[0] for d in s['documents']]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
