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

"""Attach MKM-XV-001's documentation PDF to its ModelRisk record.

The model document is generated in PhysicalRisk
(``docs/models/prs_xva/MKM-XV-001_model_document.pdf``, built from the
validation evidence in ``docs/xva/validation_evidence.json``) and filed here in
the categories the other models use. Run after ``scripts.register_xv001``.

Idempotent: a document whose stored name is already attached is skipped, so the
script is safe to re-run.

Run as:  python -m scripts.attach_xv001_docs
"""
from __future__ import annotations

from pathlib import Path

from config.paths import PRODUCER_ROOT as PHYS_ROOT
from src.governance.documents import add_document
from src.governance.model_inventory import get_model, rebuild_inventory_view
from src.governance.model_inventory.commands import AGGREGATE_TYPE as MODEL_AGGREGATE

ACTOR = "attach_xv001_docs"
MODEL_ID = "MKM-XV-001"
_DOC = "docs/models/prs_xva/MKM-XV-001_model_document.pdf"

# (category, stored filename, source path relative to PhysicalRisk root, description).
# The model document carries the test and sensitivity evidence, so it is filed
# under each category the other models use for them, as EF-001's results are.
DOCS = [
    ("Core Documentation", "prs_xva.pdf", _DOC, "PRS XVA Model Documentation"),
    ("Test Results", "test_results.pdf", _DOC, "Test Results - PRS XVA Model"),
    ("Sensitivity", "sensitivity_analysis.pdf", _DOC, "Sensitivity Analysis - PRS XVA Model"),
]


def apply(docs=DOCS, phys_root: Path = PHYS_ROOT, config=None) -> dict:
    """Attach each document to MKM-XV-001, skipping any already present.

    Returns a summary of what was attached.
    """
    model = get_model(MODEL_ID, config=config)
    if model is None:
        raise RuntimeError(
            f"{MODEL_ID} is not registered; run scripts.register_xv001 first.")

    have = {(d.get("original_name") or d.get("filename"))
            for d in (model["data"].get("documents") or [])}

    attached = []
    for category, stored_name, relpath, description in docs:
        if stored_name in have:
            continue
        data = Path(phys_root, relpath).read_bytes()
        add_document(
            aggregate_type=MODEL_AGGREGATE, aggregate_id=MODEL_ID,
            scope=f"model/{MODEL_ID}", category=category, filename=stored_name,
            data=data, description=description, actor=ACTOR, config=config)
        attached.append((category, stored_name))

    rebuild_inventory_view(config=config)
    return {"attached": attached}


def main() -> int:
    from src.database import run_migrations

    run_migrations()
    result = apply()
    if result["attached"]:
        for category, name in result["attached"]:
            print(f"  attached [{category}] {name}")
    else:
        print("MKM-XV-001 documents already attached; nothing to do.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
