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

"""File the model-specific sensitivity analyses into their ModelRisk records.

Three models reached ModelRisk with an empty Sensitivity tab. Genuine, closed-
form sensitivity analyses were built against each model's own equations in
PhysicalRisk (``models.floodrisk.sensitivity``, ``models.stress.sensitivity`` and
``models.typhoon.wind_field.sensitivity``) and rendered to PDF under
``docs/models/<folder>/``. This files each into the matching per-model Sensitivity
category, using the same stored name convention as the other models
(``sensitivity_analysis.pdf``).

Idempotent: a document whose stored name is already attached is skipped, so the
script is safe to re-run.

Run as:  python -m scripts.attach_sensitivity_docs
"""
from __future__ import annotations

from pathlib import Path

from config.paths import PRODUCER_ROOT as PHYS_ROOT
from src.governance.documents import add_document
from src.governance.model_inventory import get_model, rebuild_inventory_view
from src.governance.model_inventory.commands import AGGREGATE_TYPE as MODEL_AGGREGATE

ACTOR = "attach_sensitivity_docs"

# model_id -> (source path relative to PhysicalRisk root, description).
# Stored name is the shared convention "sensitivity_analysis.pdf" for all models.
STORED_NAME = "sensitivity_analysis.pdf"
DOCS = {
    "MKM-PF-001": (
        "docs/models/property_flood_response/pf001_depth_sensitivity_analysis.pdf",
        "Sensitivity Analysis - Property Flood Response (depth)"),
    "MKM-ST-001": (
        "docs/models/stressm_pipeline/st001_threshold_sensitivity_analysis.pdf",
        "Sensitivity Analysis - Stress Test Pipeline (severe threshold)"),
    "MKM-TC-001": (
        "docs/models/typhoon/tc001_windfield_sensitivity_analysis.pdf",
        "Sensitivity Analysis - Tropical Cyclone Wind-Field (intensity & track)"),
}


def apply(docs=DOCS, phys_root: Path = PHYS_ROOT, config=None) -> dict:
    """Attach each model's sensitivity PDF, skipping any already present."""
    attached = []
    for model_id, (relpath, description) in docs.items():
        model = get_model(model_id, config=config)
        if model is None:
            raise RuntimeError(f"{model_id} is not registered.")
        have = {(d.get("original_name") or d.get("filename"))
                for d in (model["data"].get("documents") or [])}
        if STORED_NAME in have:
            continue
        add_document(
            aggregate_type=MODEL_AGGREGATE, aggregate_id=model_id,
            scope=f"model/{model_id}", category="Sensitivity",
            filename=STORED_NAME, data=Path(phys_root, relpath).read_bytes(),
            description=description, actor=ACTOR, config=config)
        attached.append((model_id, STORED_NAME))
    rebuild_inventory_view(config=config)
    return {"attached": attached}


def main() -> int:
    from src.database import run_migrations

    run_migrations()
    result = apply()
    if result["attached"]:
        for model_id, name in result["attached"]:
            print(f"  attached [Sensitivity] {name} -> {model_id}")
    else:
        print("Sensitivity documents already attached; nothing to do.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
