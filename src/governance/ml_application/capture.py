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
"""Recording a train reported by the code that performed it.

Everything a fit can say about itself is a fact rather than a judgement, so a human
retyping it adds nothing but the chance of a typo. What the owner must still write --
the target definition, the intended and excluded uses, why the split does not leak --
is refused here on purpose: an argument is not captured, it is made.

Re-reporting the same ``fit_id`` UPDATES that train. A run that reports twice must not
become two trains, and a run that crashes after reporting must be able to report again.
"""
from __future__ import annotations

from typing import Any

from config.governance import TRAINING_FIELD_SPECS, TRAINING_RUNS_COLLECTION
from config.governance._ml_training import CAPTURABLE_FIELDS, CAPTURED_FIELD
from src.governance.errors import DomainError
from src.governance.ml_application.commands import (add_collection_item,
                                                    update_collection_item)
from src.governance.ml_application.projection import (get_ml_application,
                                                     rebuild_ml_application_view)


def _existing(record: dict, fit_id: str) -> dict | None:
    for item in (record.get("data") or {}).get(TRAINING_RUNS_COLLECTION) or []:
        if str(item.get("fit_id") or "") == fit_id:
            return item
    return None


def record_train(*, ml_application_id: str, fit_id: str, fields: dict[str, Any],
                 actor: str, config=None) -> tuple[str, bool]:
    """Create or update the train; return ``(item_id, created)``.

    A field the platform does not mark capturable is REFUSED by name rather than
    dropped: a producer that believes it recorded the split rationale, and did not,
    has been told something false about its own evidence.
    """
    record = get_ml_application(ml_application_id, config=config)
    if record is None:
        raise DomainError(f"ML Application {ml_application_id} is not registered")

    unknown = [k for k in fields if k not in TRAINING_FIELD_SPECS]
    if unknown:
        raise DomainError("not training fields: " + ", ".join(sorted(unknown)))
    judgement = [k for k in fields if k not in CAPTURABLE_FIELDS]
    if judgement:
        raise DomainError(
            "these are the owner's to write, not the run's to report: "
            + ", ".join(sorted(judgement)))

    values = {k: ("" if v is None else str(v)) for k, v in fields.items()}
    existing = _existing(record, fit_id)
    # Which fields arrived by capture, kept across re-reports so a value captured once
    # is not later mistaken for one somebody typed.
    was = set((existing or {}).get(CAPTURED_FIELD, "").split(",")) if existing else set()
    values[CAPTURED_FIELD] = ",".join(sorted({k for k in values} | {w for w in was if w}))

    # The read model is rebuilt after writing because the NEXT report reads it to
    # find this train. A long fit reports as it progresses, and a stale projection
    # would make each report a new train.
    if existing:
        update_collection_item(ml_application_id=ml_application_id,
                               collection=TRAINING_RUNS_COLLECTION,
                               item_id=existing["item_id"], fields=values, actor=actor,
                               reason=f"Captured from the run reporting {fit_id}")
        rebuild_ml_application_view(config=config)
        return existing["item_id"], False
    values["fit_id"] = fit_id
    event = add_collection_item(ml_application_id=ml_application_id,
                                collection=TRAINING_RUNS_COLLECTION, fields=values,
                                actor=actor, reason=f"Train {fit_id} reported by the run")
    rebuild_ml_application_view(config=config)
    return event.payload.get("item_id", ""), True
