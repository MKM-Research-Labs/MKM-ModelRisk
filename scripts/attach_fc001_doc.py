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

"""File MKM-FC-001's model documentation v2.2 on its ModelRisk record.

The document is generated in PhysicalRisk
(``docs/models/flood_classifier/flood_classifier.pdf``) and now carries the GBM
challenger comparison, whose results are illustrative, not sign-off evidence.
It is filed under Core Documentation, and the earlier filing moves to History,
keeping its id.

Idempotent: a document whose stored name is already attached is skipped, so the
script is safe to re-run.

Run as:  python -m scripts.attach_fc001_doc
"""
from __future__ import annotations

from pathlib import Path

from config.governance._documents import HISTORY_DOC_CATEGORY
from config.paths import PRODUCER_ROOT as PHYS_ROOT
from src.governance.documents import add_document, update_document
from src.governance.model_inventory import get_model, rebuild_inventory_view
from src.governance.model_inventory.commands import AGGREGATE_TYPE as MODEL_AGGREGATE

ACTOR = "attach_fc001_doc"
MODEL_ID = "MKM-FC-001"
CATEGORY = "Core Documentation"
SOURCE = "docs/models/flood_classifier/flood_classifier.pdf"
EARLIER_NAME = "flood_classifier.pdf"
STORED_NAME = "flood_classifier_v2.2.pdf"
DESCRIPTION = ("Flood Probability Classifier Documentation v2.2 - adds the GBM "
               "challenger comparison (illustrative results, outcome escalate)")


def apply(phys_root: Path = PHYS_ROOT, config=None) -> dict:
    """File v2.2 unless present, and retire the earlier filing to History.

    Returns a summary of what changed.
    """
    model = get_model(MODEL_ID, config=config)
    if model is None:
        raise RuntimeError(f"{MODEL_ID} is not registered.")

    documents = model["data"].get("documents") or []
    changed = []
    if STORED_NAME not in {d.get("original_name") or d.get("filename") for d in documents}:
        add_document(
            aggregate_type=MODEL_AGGREGATE, aggregate_id=MODEL_ID,
            scope=f"model/{MODEL_ID}", category=CATEGORY, filename=STORED_NAME,
            data=Path(phys_root, SOURCE).read_bytes(), description=DESCRIPTION,
            actor=ACTOR, config=config)
        changed.append((CATEGORY, STORED_NAME))
    for d in documents:
        if d.get("original_name") == EARLIER_NAME and d.get("category") == CATEGORY:
            update_document(
                aggregate_type=MODEL_AGGREGATE, aggregate_id=MODEL_ID, item_id=d["item_id"],
                fields={"category": HISTORY_DOC_CATEGORY}, actor=ACTOR, config=config,
                reason=f"Superseded by {STORED_NAME}")
            changed.append((HISTORY_DOC_CATEGORY, EARLIER_NAME))
    rebuild_inventory_view(config=config)
    return {"attached": changed}


def main() -> int:
    from src.database import run_migrations

    run_migrations()
    result = apply()
    if result["attached"]:
        for category, name in result["attached"]:
            print(f"  attached [{category}] {name}")
    else:
        print(f"{STORED_NAME} already attached to {MODEL_ID}; nothing to do.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
