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
script is safe to re-run. A REGENERATED benchmark is therefore not re-filed
under the same name -- file it as a new version deliberately.

The benchmarks are read from ``PRODUCER_ROOT``, by default the PhysicalRisk
checkout beside this one. Run from a worktree, "beside" is the worktrees
folder, so set PRODUCER_ROOT to the PhysicalRisk checkout explicitly.

Run as:  python -m scripts.attach_wolfram_benchmark [MODEL_ID ...]   (default: all)
"""
from __future__ import annotations

import sys
from pathlib import Path

from config.governance._documents import BENCHMARK_DOC_CATEGORY
from config.paths import PRODUCER_ROOT as PHYS_ROOT
from src.governance.documents import add_document
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
}


def apply(model_ids=None, benchmarks=BENCHMARKS, phys_root: Path = PHYS_ROOT,
          config=None) -> dict:
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
    if missing:
        raise FileNotFoundError(
            f"Benchmark output not found under {phys_root}: {', '.join(missing)}. "
            "Run python -m tools.wolfram_oracle <model> in PhysicalRisk, or set PRODUCER_ROOT.")

    attached = []
    for model_id in ids:
        relpath, description = benchmarks[model_id]
        stored_name = Path(relpath).name
        have = {(d.get("original_name") or d.get("filename"))
                for d in (models[model_id]["data"].get("documents") or [])}
        if stored_name in have:
            continue
        add_document(
            aggregate_type=MODEL_AGGREGATE, aggregate_id=model_id,
            scope=f"model/{model_id}", category=BENCHMARK_DOC_CATEGORY, filename=stored_name,
            data=Path(phys_root, relpath).read_bytes(), description=description,
            actor=ACTOR, config=config)
        attached.append((model_id, stored_name))

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
