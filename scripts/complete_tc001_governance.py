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

"""Close the completeness-audit gaps on MKM-TC-001 (Tropical Cyclone Wind-Field).

The record already carries a description, a nine-entry version history, a Test
Results document, interoperability handovers and (as of 2026-07-30) a sensitivity
analysis. What is missing is the validation/recertification dates, the three test
declarations, a change history, a Unit Test document, and honest assessments for
the seven unrecorded validation questions.

This fills those, honestly and idempotently, following the same pattern as the
EF/GH/PF/ST completions:

* validation_date is set to 2026-05-27 (the model reached its end-to-end pipeline
  at version 0.7.0 on that date per the existing version history) with a one-year
  recertification to 2027-05-27;
* unit_tests and integration_tests are declared ``Yes`` — a unit suite passes and
  handovers to MKM-WD-001 and MKM-WS-001 are on record; benchmark_tests is ``No``
  (no benchmark evidence exists — kept consistent with VQ-008 below);
* a two-entry change history is added from the real version milestones;
* the existing typhoon test-results PDF is filed as Unit Test evidence (filed, not
  regenerated);
* the seven unrecorded validation questions are assessed on their merits — the
  genuinely satisfied ones move up, while override controls, data quality,
  benchmarking and independent validation stay "Not Addressed" with a rationale,
  the honest basis for the model's Red rating.

Idempotent: scalars already set are left alone, an attached document is skipped, a
change-history entry already present is skipped, and a validation question already
at its target status is untouched.

Run as:  python -m scripts.complete_tc001_governance
"""
from __future__ import annotations

from pathlib import Path

from config.paths import PRODUCER_ROOT as PHYS_ROOT
from src.governance.documents import add_document
from src.governance.model_inventory import (
    add_collection_item,
    get_model,
    rebuild_inventory_view,
    update_collection_item,
    update_model_field,
)
from src.governance.model_inventory.commands import AGGREGATE_TYPE as MODEL_AGGREGATE

ACTOR = "complete_tc001_governance"
MODEL_ID = "MKM-TC-001"

# --- Scalar fields (only written if currently blank) ------------------------
SCALARS = {
    "validation_date": "2026-05-27",
    "recertification_date": "2027-05-27",
    "unit_tests": "Yes",
    "integration_tests": "Yes",
    "benchmark_tests": "No",
}

# --- Change history (version_history already exists; change_history is blank) -
CHANGES = [
    {"version": "0.6.0", "date": "2026-05-27", "author": "David K Kelly",
     "description": "Parametric wind-field forward model added (Phase 1.6): "
                    "symmetric radial profile with a gale-anchored outer decay "
                    "length, on neutralised test geography."},
    {"version": "0.7.0", "date": "2026-05-27", "author": "David K Kelly",
     "description": "End-to-end SMC pipeline and app.py port --typhoon CLI "
                    "wiring (Phase 1.7); per-location peak-wind summaries."},
]

# --- Validation questions: record the unassessed seven, honestly ------------
# VQ-006/007 are already Addressed on the live record; they are listed so a
# freshly-registered model (which seeds them without a rationale) is also
# completed — the idempotency guard leaves the live rows untouched.
VQ_UPDATES = {
    "VQ-001": ("Addressed",
        "Implements the documented methodology: a Bayesian state-space model of "
        "tropical-cyclone progression (genesis prior, one-step transition, SMC "
        "particle filter) coupled to a parametric radial wind-field, producing "
        "probabilistic trajectories and per-location peak-wind distributions — "
        "its stated purpose."),
    "VQ-002": ("Partially Addressed",
        "The pipeline is seeded and its unit suite passes, and the SMC filter and "
        "radial profile are standard, stable constructions. Track and intensity "
        "accuracy are unvalidated on synthetic tracks and there is no back-testing "
        "against historical typhoons — hence partial."),
    "VQ-003": ("Addressed",
        "The SMC particle filter is the heaviest step but is bounded by a fixed "
        "particle count and runs as a batch; no excessive computational resource "
        "use in a normal run."),
    "VQ-006": ("Addressed",
        "The model's assumptions are documented and justified in the Assumptions "
        "register on this record."),
    "VQ-007": ("Addressed",
        "The model's limitations are documented and monitored in the Limitations "
        "register on this record, with monitoring triggers."),
    "VQ-004": ("Not Addressed",
        "Controls over manual overrides are not documented; the wind-field and "
        "filter tunables are configuration values rather than governed, logged "
        "overrides. Outstanding."),
    "VQ-005": ("Not Addressed",
        "Input-data quality is not assured: the model runs on synthetic genesis "
        "and track inputs whose realism is unvalidated. Data-quality controls are "
        "outstanding."),
    "VQ-008": ("Not Addressed",
        "The model has not been benchmarked against credible alternatives (e.g. a "
        "Holland wind-field or an operational track model); no benchmark evidence "
        "is on record (benchmark_tests declared No)."),
    "VQ-009": ("Not Addressed",
        "Not independently validated; this is the basis for the current Red "
        "rating. Independent validation is outstanding."),
}

# --- Documents: file the existing test evidence as Unit Test -----------------
# (Test Results is already on the record; the same PDF is filed as unit evidence.)
DOCS = [
    ("Unit Test", "unit_tests_MKM-TC-001.pdf",
     "docs/models/typhoon/test_results.pdf",
     "Unit test evidence - Tropical Cyclone Progression and Wind-Field"),
]


def apply(phys_root: Path = PHYS_ROOT, config=None) -> dict:
    """Fill the audited gaps idempotently; return a summary."""
    model = get_model(MODEL_ID, config=config)
    if model is None:
        raise RuntimeError(f"{MODEL_ID} is not registered.")
    data = model["data"]
    summary = {"fields": [], "changes": 0, "questions": 0, "documents": []}

    for field, value in SCALARS.items():
        if data.get(field) in (None, "", "None"):
            update_model_field(model_id=MODEL_ID, field=field, value=value,
                               actor=ACTOR, config=config,
                               reason="Complete audited governance record")
            summary["fields"].append(field)

    have_changes = {(c.get("version"), c.get("description"))
                    for c in (data.get("change_history") or [])}
    for entry in CHANGES:
        if (entry["version"], entry["description"]) not in have_changes:
            add_collection_item(model_id=MODEL_ID, collection="change_history",
                                fields=entry, actor=ACTOR, config=config)
            summary["changes"] += 1

    by_id = {q["item_id"]: q for q in data.get("validation_questions", [])}
    for item_id, (status, rationale) in VQ_UPDATES.items():
        current = by_id.get(item_id)
        if current is not None and (
                current.get("status") != status or not current.get("rationale")):
            update_collection_item(
                model_id=MODEL_ID, collection="validation_questions",
                item_id=item_id, fields={"status": status, "rationale": rationale},
                actor=ACTOR, config=config, reason="Validation assessment update")
            summary["questions"] += 1

    have = {(d.get("original_name") or d.get("filename"))
            for d in (data.get("documents") or [])}
    for category, stored_name, relpath, description in DOCS:
        if stored_name in have:
            continue
        add_document(
            aggregate_type=MODEL_AGGREGATE, aggregate_id=MODEL_ID,
            scope=f"model/{MODEL_ID}", category=category, filename=stored_name,
            data=Path(phys_root, relpath).read_bytes(), description=description,
            actor=ACTOR, config=config)
        summary["documents"].append((category, stored_name))

    rebuild_inventory_view(config=config)
    return summary


def main() -> int:
    from src.database import run_migrations

    run_migrations()
    s = apply()
    print(f"TC-001 record: +fields {s['fields']}, {s['changes']} change-history "
          f"entries, {s['questions']} validation questions recorded, +docs "
          f"{[d[0] for d in s['documents']]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
