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

"""Phase 2 of the Test Results backlog: per-model governance completion.

Phase 1 (``scripts.file_test_results_backlog``) filed test evidence and set the
test declarations for 17 models. Phase 2 completes the remaining governance
fields — the validation date and the seven unrecorded validation questions — which
need per-model judgement and so are done in tranches, not one sweep.

Each model's validation_date is anchored to its real final-version date (from the
existing version history); recertification dates and version/change history are
already populated on these records, so they are left untouched. The validation
questions are assessed on each model's actual behaviour: the genuinely satisfied
ones move up, while override controls, data quality, benchmarking and independent
validation stay "Not Addressed" with a rationale — the honest basis for each Red
rating. VQ-006/007 (assumptions, limitations) are already Addressed on the live
records and are listed only so a freshly-registered model is also completed; the
idempotency guard leaves the live rows untouched.

Tranche 1: the flood-hazard chain — DD, FPO, FC, SP, SG.
Tranche 2: BRI, DE, FIRE, GHD, IP, MP.
Tranche 3: PR, PV, RA, SEIS, SI, SS — completes the 17-model backlog.
A model whose recertification_date is also blank carries one in its spec;
otherwise only the validation_date and questions are filled. Idempotent.

The per-model assessments live in ``scripts._phase2_assessments`` (rule R2);
this module is just the idempotent applier.

Run as:  python -m scripts.complete_governance_phase2
"""
from __future__ import annotations

from scripts._phase2_assessments import MODELS
from src.governance.model_inventory import (
    get_model,
    rebuild_inventory_view,
    update_collection_item,
    update_model_field,
)

ACTOR = "complete_governance_phase2"


def apply_one(model_id: str, config=None) -> dict:
    """Complete one model's validation date and validation questions idempotently."""
    spec = MODELS[model_id]
    model = get_model(model_id, config=config)
    if model is None:
        raise RuntimeError(f"{model_id} is not registered.")
    data = model["data"]
    summary = {"model": model_id, "fields": [], "questions": 0}

    scalars = {"validation_date": spec["validation_date"]}
    if "recertification_date" in spec:
        scalars["recertification_date"] = spec["recertification_date"]
    for field, value in scalars.items():
        if data.get(field) in (None, "", "None"):
            update_model_field(model_id=model_id, field=field, value=value,
                               actor=ACTOR, config=config,
                               reason="Complete audited governance record (Phase 2)")
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

    rebuild_inventory_view(config=config)
    return summary


def apply(config=None) -> list[dict]:
    """Complete every model in the current tranche; return per-model summaries."""
    return [apply_one(mid, config=config) for mid in MODELS]


def main() -> int:
    from src.database import run_migrations

    run_migrations()
    for s in apply():
        print(f"{s['model']}: +fields {s['fields']}, {s['questions']} validation "
              "questions recorded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
