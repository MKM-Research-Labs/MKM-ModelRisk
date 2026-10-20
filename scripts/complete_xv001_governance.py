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

"""Close the record-level governance gaps a completeness audit found on MKM-XV-001.

XV-001 was registered at WP0 and brought to its built state, but reached the
audit with no description, rationales, data sources, evaluations, RACI or
version history, every validation question Not Addressed, and its model
document filed under three categories only. This fills those in from the build
evidence (see ``_xv001_completion``), never inflated.

Left open on purpose, because the work has not happened: validation date, last
review, MRC sign-off and recertification, the sign-off history, and the peer
reviewer (a named person other than the owner, for the owner to choose).
Monitoring and segment-analysis documents are not covered by the model document.

Idempotent: a scalar already set is left alone, an item already present is
skipped, and a validation question already at its target status is untouched.

Run as:  python -m scripts.complete_xv001_governance
"""
from __future__ import annotations

from scripts import _xv001_completion as data
from scripts import attach_xv001_docs
from src.governance.model_inventory import (
    add_collection_item,
    get_model,
    rebuild_inventory_view,
    update_collection_item,
    update_model_field,
)

ACTOR = "complete_xv001_governance"
MODEL_ID = "MKM-XV-001"
REASON = "Complete audited governance record"

# collection -> (items, the field that identifies an item already present)
COLLECTIONS = {
    "version_history": (data.VERSIONS, "version"),
    "change_history": (data.CHANGES, "description"),
    "data_sources": (data.DATA_SOURCES, "data_source"),
    "evaluations": (data.EVALUATIONS, "dataset"),
    "raci_roles": (data.RACI_ROLES, "role"),
    "fairness_assessments": (data.FAIRNESS, "attribute"),
}


def _blank(value) -> bool:
    return value in (None, "", "None")


def apply(config=None, phys_root=None) -> dict:
    """Fill the audited record gaps idempotently; return a summary."""
    # Fold in writes from an earlier run that stopped before its final rebuild,
    # so they are seen as present and not written again.
    rebuild_inventory_view(config=config)
    model = get_model(MODEL_ID, config=config)
    if model is None:
        raise RuntimeError(f"{MODEL_ID} is not registered.")
    record = model["data"]
    summary = {"fields": [], "items": {}, "questions": 0, "documents": []}

    for field, value in data.SCALARS.items():
        if _blank(record.get(field)):
            update_model_field(model_id=MODEL_ID, field=field, value=value,
                               actor=ACTOR, config=config, reason=REASON)
            summary["fields"].append(field)
    if record.get("version") == data.VERSION_FROM:
        update_model_field(model_id=MODEL_ID, field="version", value=data.VERSION_TO,
                           actor=ACTOR, config=config,
                           reason="WP6 term-structure fit; model document v0.10")
        summary["fields"].append("version")

    for collection, (items, key) in COLLECTIONS.items():
        have = {item.get(key) for item in record.get(collection, [])}
        added = 0
        for item in items:
            if item[key] not in have:
                add_collection_item(model_id=MODEL_ID, collection=collection,
                                    fields=item, actor=ACTOR, config=config)
                added += 1
        summary["items"][collection] = added

    by_id = {q["item_id"]: q for q in record.get("validation_questions", [])}
    for item_id, (status, rationale) in data.VQ_UPDATES.items():
        current = by_id.get(item_id)
        if current is not None and current.get("status") != status:
            update_collection_item(
                model_id=MODEL_ID, collection="validation_questions",
                item_id=item_id, fields={"status": status, "rationale": rationale},
                actor=ACTOR, config=config, reason="First-line validation assessment")
            summary["questions"] += 1

    docs = [(category, name, attach_xv001_docs._DOC, description)
            for category, name, description in data.EXTRA_DOCS]
    kwargs = {} if phys_root is None else {"phys_root": phys_root}
    summary["documents"] = attach_xv001_docs.apply(docs=docs, config=config,
                                                   **kwargs)["attached"]

    rebuild_inventory_view(config=config)
    return summary


def main() -> int:
    from src.database import run_migrations

    run_migrations()
    s = apply()
    print(f"XV-001 record: +fields {s['fields']}, +items {s['items']}, "
          f"{s['questions']} validation questions updated, "
          f"+documents {[c for c, _ in s['documents']]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
