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
"""Which folder under ``docs/models/`` holds each model's documentation.

The source inventory's ``documents[].path`` is unreliable: for most models it is
absent, and for MKM-IP-001 it points into another model's folder. Each entry below
was instead confirmed from the title page of the PDF in that folder, so the mapping
is evidence rather than a guess at folder names. It takes precedence over the
inventory path; models absent here fall back to whatever the inventory says.

Confirmed titles, in folder order: "Gauge Historical Daily Synthetic Generation
Model", "Insurance Premium Model", "Property Flood Response Model", "Property
Valuation Model", "Spatial Interpolation Model", "Storm Sequence Generator ...
(MKM-SS-001)", "Stress Test Pipeline", "Building Fire-Resilience Credit Model",
"Building Seismic-Resilience Credit Model", "Tropical Cyclone Progression and
Wind-Field - Test Results".

MKM-BRF-001, MKM-WS-001 and MKM-WD-001 are deliberately absent: they have no
documentation in the source at all.
"""

from pathlib import Path

MODEL_FOLDERS = {
    "MKM-GHD-001": "gaugehd_synthetic",
    "MKM-IP-001": "insurance_premium",
    "MKM-PF-001": "property_flood_response",
    "MKM-PV-001": "property_valuation",
    "MKM-SP-001": "spatial_model",
    "MKM-SS-001": "storm_multi",
    "MKM-ST-001": "stressm_pipeline",
    "MKM-FIRE-001": "fire_resilience",
    "MKM-SEIS-001": "seismic_resilience",
    "MKM-TC-001": "typhoon",
}


def folder_for(model: dict, phys_root: Path, models_root: Path) -> Path | None:
    """The documentation folder for one source model, or ``None`` if it has none:
    the confirmed mapping above first, then whatever its inventory paths resolve to."""
    named = MODEL_FOLDERS.get(model.get("model_id"))
    if named and (models_root / named).is_dir():
        return models_root / named
    for doc in model.get("documents") or []:
        path = doc.get("path") if isinstance(doc, dict) else None
        if path and (phys_root / path).is_file():
            return (phys_root / path).parent
    return None
