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

"""Attach each model's Wolfram oracle benchmark to its ModelRisk record.

The benchmarks are generated in PhysicalRisk by ``python -m tools.wolfram_oracle
<model>``, each a LaTeX document on the house template under
``docs/models/<model>_benchmark/``. Only the PDF is filed, as a Benchmark Test,
which the Docs tab lists on its own Benchmark panel; the CSVs beside it stay in
PhysicalRisk, where the numbers behind the PDF can be regenerated.

Idempotent: a document whose stored name is already attached is skipped, so the
script is safe to re-run. A REGENERATED benchmark is filed as a new version: its
entry names a versioned stored name, and the earlier filing of the same PDF
(stored under the PDF's own name) moves from Benchmark to History, keeping its id.
A first issue superseded before it was filed is kept as evidence of checking: it is
read from the producer's git history and filed straight to History (ORIGINALS).

The benchmarks are read from ``PRODUCER_ROOT``, by default the PhysicalRisk
checkout beside this one. Run from a worktree, "beside" is the worktrees
folder, so set PRODUCER_ROOT to the PhysicalRisk checkout explicitly.

Run as:  python -m scripts.attach_wolfram_benchmark [MODEL_ID ...]   (default: all)
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from config.governance._documents import BENCHMARK_DOC_CATEGORY, HISTORY_DOC_CATEGORY
from config.paths import PRODUCER_ROOT as PHYS_ROOT
from src.governance.documents import add_document, update_document
from src.governance.model_inventory import get_model, rebuild_inventory_view
from src.governance.model_inventory.commands import AGGREGATE_TYPE as MODEL_AGGREGATE

ACTOR = "attach_wolfram_benchmark"

# Model -> (its benchmark PDF under PRODUCER_ROOT, description). The PDF is filed
# under its own name, which says Wolfram produced it.
BENCHMARKS = {
    "MKM-GH-001": ("docs/models/gev_hazard_benchmark/MKM-GH-001_wolfram_benchmark.pdf",
                   "Wolfram oracle benchmark - GEV Hazard Curve Model"),
    "MKM-PR-001": ("docs/models/prs_pricing_benchmark/MKM-PR-001_wolfram_benchmark.pdf",
                   "Wolfram oracle benchmark - PRS Analytical Pricing Model"),
    "MKM-SI-001": ("docs/models/storm_intensity_benchmark/MKM-SI-001_wolfram_benchmark.pdf",
                   "Wolfram oracle benchmark - Storm Intensity Distribution"),
    "MKM-DE-001": ("docs/models/delta_engine_benchmark/MKM-DE-001_wolfram_benchmark.pdf",
                   "Wolfram oracle benchmark v0.2 - Delta Engine, after the MTM and floor fixes",
                   "MKM-DE-001_wolfram_benchmark_v0.2.pdf"),
    "MKM-EF-001": ("docs/models/event_frequency_benchmark/MKM-EF-001_wolfram_benchmark.pdf",
                   "Wolfram oracle benchmark v0.2 - Event Frequency Model, after the term-structure fix",
                   "MKM-EF-001_wolfram_benchmark_v0.2.pdf"),
    "MKM-FIRE-001": ("docs/models/fire_resilience_benchmark/MKM-FIRE-001_wolfram_benchmark.pdf",
                     "Wolfram oracle benchmark - Building Fire-Resilience Credit Model"),
    "MKM-SEIS-001": ("docs/models/seismic_resilience_benchmark/MKM-SEIS-001_wolfram_benchmark.pdf",
                     "Wolfram oracle benchmark - Building Seismic-Resilience Credit Model"),
    "MKM-GHD-001": ("docs/models/gauge_historical_benchmark/MKM-GHD-001_wolfram_benchmark.pdf",
                    "Wolfram oracle benchmark - Gauge Historical Daily Synthetic Generation Model"),
    "MKM-DD-001": ("docs/models/depth_damage_benchmark/MKM-DD-001_wolfram_benchmark.pdf",
                   "Wolfram oracle benchmark v0.2 - Depth-Damage Curve Model, against documentation v2.0"),
    "MKM-FPO-001": ("docs/models/flood_poly_benchmark/MKM-FPO-001_wolfram_benchmark.pdf",
                    "Wolfram oracle benchmark v0.2 - Flood Polynomial Model, against documentation v2.0"),
    "MKM-SG-001": ("docs/models/storm_gauge_benchmark/MKM-SG-001_wolfram_benchmark.pdf",
                   "Wolfram oracle benchmark v0.2 - Storm-Gauge Forward Model, against documentation v2.0"),
    "MKM-SP-001": ("docs/models/spatial_benchmark/MKM-SP-001_wolfram_benchmark.pdf",
                   "Wolfram oracle benchmark v0.2 - Spatial Interpolation Model, against documentation v2.0"),
    "MKM-SS-001": ("docs/models/storm_sequence_benchmark/MKM-SS-001_wolfram_benchmark.pdf",
                   "Wolfram oracle benchmark v0.2 - Storm Sequence Generator, against documentation v3.0"),
    "MKM-MP-001": ("docs/models/mortgage_pricing_benchmark/MKM-MP-001_wolfram_benchmark.pdf",
                   "Wolfram oracle benchmark v0.2 - Mortgage Pricing Model, after the fair-value fix",
                   "MKM-MP-001_wolfram_benchmark_v0.2.pdf"),
}
# A third item, where present, is the versioned name to file under; the filing
# under the PDF's own name is then an earlier version, retired to History.

# Originals kept as evidence of checking: a first issue that was superseded before
# it was filed, read from the producer's git history at the commit that issued it
# and filed straight to History under a versioned name, beside the current one.
# Model -> (commit, PDF path at that commit, stored name, description).
ORIGINALS = {
    "MKM-DD-001": ("23363b89aad7ee2faaaa22ece6e591cc212af2b0",
                   "docs/models/depth_damage_benchmark/MKM-DD-001_wolfram_benchmark.pdf",
                   "MKM-DD-001_wolfram_benchmark_v0.1.pdf",
                   "Wolfram oracle benchmark v0.1 - Depth-Damage Curve Model, against the filed "
                   "documentation v1.1; found it no longer described the model (superseded by v0.2)"),
    "MKM-FPO-001": ("fcd060afa5894f47efdeda35cc530b43a86de885",
                    "docs/models/flood_poly_benchmark/MKM-FPO-001_wolfram_benchmark.pdf",
                    "MKM-FPO-001_wolfram_benchmark_v0.1.pdf",
                    "Wolfram oracle benchmark v0.1 - Flood Polynomial Model, against the filed "
                    "documentation v1.0; found its evidence did not hold (superseded by v0.2)"),
    "MKM-SG-001": ("822deb06443d5c5486b280db875932dbb9c9f8ba",
                   "docs/models/storm_gauge_benchmark/MKM-SG-001_wolfram_benchmark.pdf",
                   "MKM-SG-001_wolfram_benchmark_v0.1.pdf",
                   "Wolfram oracle benchmark v0.1 - Storm-Gauge Forward Model, against the filed "
                   "documentation v1.3; found 8 of its 16 claims did not hold (superseded by v0.2)"),
    "MKM-SP-001": ("9f9b3eb6685343ff383a2171f61d4a32c1b1edec",
                   "docs/models/spatial_benchmark/MKM-SP-001_wolfram_benchmark.pdf",
                   "MKM-SP-001_wolfram_benchmark_v0.1.pdf",
                   "Wolfram oracle benchmark v0.1 - Spatial Interpolation Model, against the filed "
                   "documentation v1.0; found 10 of its 15 claims did not hold (superseded by v0.2)"),
    "MKM-SS-001": ("65c6aaa74fe7b46d1b176bccc1f5b4c211766363",
                   "docs/models/storm_sequence_benchmark/MKM-SS-001_wolfram_benchmark.pdf",
                   "MKM-SS-001_wolfram_benchmark_v0.1.pdf",
                   "Wolfram oracle benchmark v0.1 - Storm Sequence Generator, against the filed "
                   "documentation v2.0; found 11 of its 17 claims did not hold (superseded by v0.2)"),
}


def _original_bytes(phys_root, commit: str, relpath: str) -> bytes:
    """A file as the producer committed it."""
    out = subprocess.run(["git", "-C", str(phys_root), "show", f"{commit}:{relpath}"],
                         capture_output=True, check=True)
    return out.stdout


def apply(model_ids=None, benchmarks=BENCHMARKS, phys_root: Path = PHYS_ROOT,
          config=None, originals=None) -> dict:
    """Attach each named model's benchmark (all by default), skipping any present.

    Every model and every source file is checked before anything is written, so
    one missing benchmark cannot leave the others half-filed.
    """
    ids = list(model_ids or benchmarks)
    unknown = [m for m in ids if m not in benchmarks]
    if unknown:
        raise KeyError(f"No benchmark is defined for: {', '.join(unknown)}")
    models = {m: get_model(m, config=config) for m in ids}
    absent = [m for m, rec in models.items() if rec is None]
    if absent:
        raise RuntimeError(f"Not registered: {', '.join(absent)}.")
    missing = [benchmarks[m][0] for m in ids if not Path(phys_root, benchmarks[m][0]).is_file()]
    attached = []
    if missing:
        raise FileNotFoundError(
            f"Benchmark output not found under {phys_root}: {', '.join(missing)}. "
            "Run python -m tools.wolfram_oracle <model> in PhysicalRisk, or set PRODUCER_ROOT.")
    originals = ORIGINALS if originals is None else originals
    kept = {m: _original_bytes(phys_root, c, rel) for m, (c, rel, _, _) in originals.items() if m in ids}

    for model_id in ids:
        relpath, description, *versioned = benchmarks[model_id]
        stored_name = versioned[0] if versioned else Path(relpath).name
        documents = models[model_id]["data"].get("documents") or []
        if model_id in kept:
            _, _, name, desc = originals[model_id]
            if name not in {d.get("original_name") or d.get("filename") for d in documents}:
                add_document(
                    aggregate_type=MODEL_AGGREGATE, aggregate_id=model_id,
                    scope=f"model/{model_id}", category=HISTORY_DOC_CATEGORY, filename=name,
                    data=kept[model_id], description=desc, actor=ACTOR, config=config)
                attached.append((model_id, f"{name} -> {HISTORY_DOC_CATEGORY}"))
        if stored_name not in {d.get("original_name") or d.get("filename") for d in documents}:
            add_document(
                aggregate_type=MODEL_AGGREGATE, aggregate_id=model_id,
                scope=f"model/{model_id}", category=BENCHMARK_DOC_CATEGORY, filename=stored_name,
                data=Path(phys_root, relpath).read_bytes(), description=description,
                actor=ACTOR, config=config)
            attached.append((model_id, stored_name))
        for d in documents if versioned else ():
            if (d.get("original_name") == Path(relpath).name
                    and d.get("category") == BENCHMARK_DOC_CATEGORY):
                update_document(
                    aggregate_type=MODEL_AGGREGATE, aggregate_id=model_id, item_id=d["item_id"],
                    fields={"category": HISTORY_DOC_CATEGORY}, actor=ACTOR, config=config,
                    reason=f"Superseded by {stored_name}")
                attached.append((model_id, f"{Path(relpath).name} -> {HISTORY_DOC_CATEGORY}"))

    rebuild_inventory_view(config=config)
    return {"attached": attached}


def main(argv=None) -> int:
    from config.database import DatabaseConfig
    from src.database import run_migrations

    print(f"Database: {DatabaseConfig.from_env().name}; reading from {PHYS_ROOT}")
    run_migrations()
    result = apply(sys.argv[1:] if argv is None else argv)
    if result["attached"]:
        for model_id, name in result["attached"]:
            print(f"  attached [{model_id}] {name}")
    else:
        print("Benchmarks already attached; nothing to do.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
