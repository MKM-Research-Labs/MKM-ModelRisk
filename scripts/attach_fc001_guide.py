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

"""Attach the stress testing guide to MKM-FC-001's ModelRisk record.

The guide is generated in PhysicalRisk
(``docs/models/stress_testing/stress_testing_guide.pdf``) and carries the GBM
challenger comparison. It is filed under Analysis, beside the model document
rather than replacing it: its results are illustrative, not sign-off evidence.

Idempotent: a document whose stored name is already attached is skipped, so the
script is safe to re-run. A later version of the guide gets a new stored name.

Run as:  python -m scripts.attach_fc001_guide
"""
from __future__ import annotations

from pathlib import Path

from config.paths import PRODUCER_ROOT as PHYS_ROOT
from src.governance.documents import add_document
from src.governance.model_inventory import get_model, rebuild_inventory_view
from src.governance.model_inventory.commands import AGGREGATE_TYPE as MODEL_AGGREGATE

ACTOR = "attach_fc001_guide"
MODEL_ID = "MKM-FC-001"
CATEGORY = "Analysis"
SOURCE = "docs/models/stress_testing/stress_testing_guide.pdf"
STORED_NAME = "stress_testing_guide_v1.2.pdf"
DESCRIPTION = ("Stress Testing Guide v1.2 - GBM challenger comparison "
               "(illustrative results, outcome escalate)")


def apply(phys_root: Path = PHYS_ROOT, config=None) -> dict:
    """Attach the guide to MKM-FC-001 unless it is already present.

    Returns a summary of what was attached.
    """
    model = get_model(MODEL_ID, config=config)
    if model is None:
        raise RuntimeError(f"{MODEL_ID} is not registered.")

    have = {(d.get("original_name") or d.get("filename"))
            for d in (model["data"].get("documents") or [])}
    if STORED_NAME in have:
        return {"attached": []}

    add_document(
        aggregate_type=MODEL_AGGREGATE, aggregate_id=MODEL_ID,
        scope=f"model/{MODEL_ID}", category=CATEGORY, filename=STORED_NAME,
        data=Path(phys_root, SOURCE).read_bytes(), description=DESCRIPTION,
        actor=ACTOR, config=config)
    rebuild_inventory_view(config=config)
    return {"attached": [(CATEGORY, STORED_NAME)]}


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
