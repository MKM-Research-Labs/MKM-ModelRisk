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

"""Phase 1 of the Test Results backlog: file existing test evidence for 17 models.

Seventeen models reached ModelRisk without a Test Results document, yet each
already has a rendered ``test_results.pdf`` on disk under PhysicalRisk
``docs/models/<folder>/`` (see ``docs/test_results_backlog_plan.md``). This is a
filing exercise, not a generation one.

For each model this fills, honestly and idempotently:

* the **Test Results** document (filed from the on-disk PDF), and
* the **Unit Test** document (the same PDF — it is unit-test evidence), and
* ``unit_tests = Yes`` (all 17), and
* ``integration_tests`` = Yes where interoperability handovers already exist, and
  No for the two models (FIRE, SEIS) that have none, and
* ``benchmark_tests = No`` for all 17 — no benchmarking has been done, so the
  Benchmark Test finding is left open rather than papered over.

It does NOT touch validation questions, dates or history — that is Phase 2, which
needs per-model judgement.

Idempotent: a scalar already set is left alone and a document already attached
(by stored name) is skipped, so the script is safe to re-run.

Run as:  python -m scripts.file_test_results_backlog
"""
from __future__ import annotations

from pathlib import Path

from config.paths import PRODUCER_ROOT as PHYS_ROOT
from src.governance.documents import add_document
from src.governance.model_inventory import (
    get_model,
    rebuild_inventory_view,
    update_model_field,
)
from src.governance.model_inventory.commands import AGGREGATE_TYPE as MODEL_AGGREGATE

ACTOR = "file_test_results_backlog"

# model_id -> (docs/models folder, model name, integration_tests declaration).
# integration_tests is "Yes" only where interoperability handovers already exist
# on the record (15 of 17); FIRE-001 and SEIS-001 have none, so "No".
MODELS = {
    "MKM-BRI-001":  ("bri_resilience",     "Building Resilience Index (BRI) Model",        "Yes"),
    "MKM-DD-001":   ("flood_risk",         "Depth-Damage Curve Model",                     "Yes"),
    "MKM-DE-001":   ("delta_engine",       "Delta Engine",                                 "Yes"),
    "MKM-FC-001":   ("flood_classifier",   "Flood Probability Classifier",                 "Yes"),
    "MKM-FIRE-001": ("fire_resilience",    "Building Fire-Resilience Credit Model",        "No"),
    "MKM-FPO-001":  ("flood_poly",         "Flood Polynomial Model",                       "Yes"),
    "MKM-GHD-001":  ("gaugehd_synthetic",  "Gauge Historical Daily",                       "Yes"),
    "MKM-IP-001":   ("insurance_premium",  "Insurance Premium Model",                      "Yes"),
    "MKM-MP-001":   ("mortgage_pricer",    "Mortgage Pricing Model",                       "Yes"),
    "MKM-PR-001":   ("prs_pricing",        "PRS Analytical Pricing Model",                 "Yes"),
    "MKM-PV-001":   ("property_valuation", "Property Valuation Model",                     "Yes"),
    "MKM-RA-001":   ("risk_assessment",    "Risk Analytics Model",                         "Yes"),
    "MKM-SEIS-001": ("seismic_resilience", "Building Seismic-Resilience Credit Model",     "No"),
    "MKM-SG-001":   ("storm_gauge",        "Storm-Gauge Response Model",                   "Yes"),
    "MKM-SI-001":   ("storm_intensity",    "Storm Intensity Distribution",                 "Yes"),
    "MKM-SP-001":   ("spatial_model",      "Spatial Interpolation Model",                  "Yes"),
    "MKM-SS-001":   ("storm_multi",        "Storm Sequence Generator",                     "Yes"),
}


def apply_one(model_id: str, phys_root: Path = PHYS_ROOT, config=None) -> dict:
    """File one model's test evidence and set its test declarations idempotently."""
    folder, name, integration = MODELS[model_id]
    model = get_model(model_id, config=config)
    if model is None:
        raise RuntimeError(f"{model_id} is not registered.")
    data = model["data"]
    summary = {"model": model_id, "fields": [], "documents": []}

    scalars = {
        "unit_tests": "Yes",
        "integration_tests": integration,
        "benchmark_tests": "No",
    }
    for field, value in scalars.items():
        if data.get(field) in (None, "", "None"):
            update_model_field(model_id=model_id, field=field, value=value,
                               actor=ACTOR, config=config,
                               reason="File test evidence (Test Results backlog, Phase 1)")
            summary["fields"].append(field)

    source = Path(phys_root, "docs", "models", folder, "test_results.pdf")
    have = {(d.get("original_name") or d.get("filename"))
            for d in (data.get("documents") or [])}
    docs = [
        ("Test Results", "test_results.pdf", f"Test Results - {name}"),
        ("Unit Test", f"unit_tests_{model_id}.pdf", f"Unit test evidence - {name}"),
    ]
    payload = None
    for category, stored_name, description in docs:
        if stored_name in have:
            continue
        if payload is None:
            payload = source.read_bytes()
        add_document(
            aggregate_type=MODEL_AGGREGATE, aggregate_id=model_id,
            scope=f"model/{model_id}", category=category, filename=stored_name,
            data=payload, description=description, actor=ACTOR, config=config)
        summary["documents"].append((category, stored_name))

    rebuild_inventory_view(config=config)
    return summary


def apply(phys_root: Path = PHYS_ROOT, config=None) -> list[dict]:
    """File all 17 models; return per-model summaries."""
    return [apply_one(mid, phys_root=phys_root, config=config) for mid in MODELS]


def main() -> int:
    from src.database import run_migrations

    run_migrations()
    filed = 0
    for s in apply():
        if s["fields"] or s["documents"]:
            filed += 1
            print(f"{s['model']}: +fields {s['fields']}, +docs {[d[0] for d in s['documents']]}")
    print(f"Done. {filed}/{len(MODELS)} models updated "
          "(re-runs are no-ops). Benchmark Test findings left open by design.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
