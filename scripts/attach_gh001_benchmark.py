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

"""Attach MKM-GH-001's Wolfram oracle benchmark to its ModelRisk record.

The benchmark is generated in PhysicalRisk by ``python -m tools.wolfram_oracle``
(``docs/models/gev_hazard_benchmark/``), a LaTeX document on the house template
(``docs/models/shared/mkm_header.tex``). Only its PDF is filed, under Analysis
beside the model's existing analysis.pdf; the CSVs that sit next to it stay in
PhysicalRisk, which is where the numbers behind the PDF can be regenerated. The
stored name is the document's own, which says Wolfram produced it and cannot
collide with analysis.pdf.

Idempotent: a document whose stored name is already attached is skipped, so the
script is safe to re-run. A REGENERATED benchmark is therefore not re-filed
under the same name — file it as a new version deliberately.

The benchmark is read from ``PRODUCER_ROOT`` (default: the PhysicalRisk checkout
beside this one). To file it from a branch that has not reached PhysicalRisk's
main, point PRODUCER_ROOT at that worktree.

Run as:  python -m scripts.attach_gh001_benchmark
"""
from __future__ import annotations

from pathlib import Path

from config.paths import PRODUCER_ROOT as PHYS_ROOT
from src.governance.documents import add_document
from src.governance.model_inventory import get_model, rebuild_inventory_view
from src.governance.model_inventory.commands import AGGREGATE_TYPE as MODEL_AGGREGATE

ACTOR = "attach_gh001_benchmark"
MODEL_ID = "MKM-GH-001"
_DIR = "docs/models/gev_hazard_benchmark"

DOCS = [
    ("Analysis", "MKM-GH-001_wolfram_benchmark.pdf", f"{_DIR}/MKM-GH-001_wolfram_benchmark.pdf",
     "Wolfram oracle benchmark - GEV Hazard Curve Model"),
]


def apply(docs=DOCS, phys_root: Path = PHYS_ROOT, config=None) -> dict:
    """Attach each document to MKM-GH-001, skipping any already present.

    Every source file is checked before anything is written, so a missing one
    cannot leave the record half-filed.
    """
    model = get_model(MODEL_ID, config=config)
    if model is None:
        raise RuntimeError(f"{MODEL_ID} is not registered.")

    missing = [rel for _, _, rel, _ in docs if not Path(phys_root, rel).is_file()]
    if missing:
        raise FileNotFoundError(
            f"Benchmark output not found under {phys_root}: {', '.join(missing)}. "
            "Run python -m tools.wolfram_oracle in PhysicalRisk, or set PRODUCER_ROOT.")

    have = {(d.get("original_name") or d.get("filename"))
            for d in (model["data"].get("documents") or [])}

    attached = []
    for category, stored_name, relpath, description in docs:
        if stored_name in have:
            continue
        add_document(
            aggregate_type=MODEL_AGGREGATE, aggregate_id=MODEL_ID,
            scope=f"model/{MODEL_ID}", category=category, filename=stored_name,
            data=Path(phys_root, relpath).read_bytes(), description=description,
            actor=ACTOR, config=config)
        attached.append((category, stored_name))

    rebuild_inventory_view(config=config)
    return {"attached": attached}


def main() -> int:
    from config.database import DatabaseConfig
    from src.database import run_migrations

    print(f"Database: {DatabaseConfig.from_env().name}; reading from {PHYS_ROOT}")
    run_migrations()
    result = apply()
    if result["attached"]:
        for category, name in result["attached"]:
            print(f"  attached [{category}] {name}")
    else:
        print("MKM-GH-001 benchmark already attached; nothing to do.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
