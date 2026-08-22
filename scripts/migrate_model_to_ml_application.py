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
"""Move a model out of the inventory and onto the ML Application register.

An institution's estate contains models that are really ML applications -- something
fitted to data, using an off-the-shelf estimator. This moves one across without
losing what the inventory holds about it.

    python -m scripts.migrate_model_to_ml_application MKM-FC-001 MLA-FC-001 \\
        GradientBoostingClassifier [actor]

Against a PROTECTED database this refuses unless the operator names that database
explicitly:

    MIGRATE_ALLOW_PROTECTED=mkm_modelrisk python -m scripts... <ids> <estimator> <actor>

The refusal is the default and stays that way. The live log is append-only -- a
migration writes roughly ninety events that can be retired by a committee but never
deleted -- so writing to it has to be something an operator states, not something a
mistyped DB_NAME can cause. And ``actor`` is required there: "migration" is not a
person in the People directory, and an event on the real estate should say who did
it.

The estimator is an ARGUMENT because the inventory does not record one -- naming what
the thing is actually built on is the information the ML register adds, and inferring
it from a methodology sentence would be a guess presented as a fact.

What does NOT come across, and why:

``dependencies``   An ML Application has no dependency chain (docs/design/mlmodel.md).
``raci_roles``     Accountability sits on the Product that consumes it.
``type``           The admin model_type describes a model's part in a Product. It says
                   nothing about an ML Application -- they are all classifiers or
                   regressors, and the Estimator already says which.

``version_history`` becomes TRAINS. An ML Application has no versions -- the record of
change is its sequence of fits -- and each version entry describes one: a date, an
author, and what changed about the model. Dropping them would lose the only history
the inventory holds of how the thing was built.

The nine SR 26-2 answers ARE carried, into the ML questionnaire. A record keeps the
questions it was actually asked; re-asking it the ML set would discard answers a
reviewer gave and a committee saw.

The source model is left exactly as it is. Retiring it is a committee's decision, not
a migration's.
"""
from __future__ import annotations

import os
import sys

from config.database import DatabaseConfig
from src.governance.errors import DomainError
from config.governance import (ML_APPLICATION_COLLECTION_SPECS, ML_APPLICATION_FIELD_SPECS,
                               ML_REVIEW_QUESTIONS_COLLECTION, TRAINING_RUNS_COLLECTION)
from src.governance.documents import (add_document, list_documents,
                                      ml_application_scope, model_scope)
from src.governance.ml_application import (add_collection_item, get_ml_application,
                                           rebuild_ml_application_view,
                                           register_ml_application,
                                           update_ml_application_field)
from src.governance.ml_application.commands import AGGREGATE_TYPE as ML_AGGREGATE
from src.governance.model_inventory import get_model
from src.governance.model_inventory.commands import AGGREGATE_TYPE as MODEL_AGGREGATE
from src.files import upload_path

PROTECTED = ("mkm_modelrisk", "mkm_modelrisk_demo")

# Model field -> ML Application field, where the two ask the same question under
# different names. Everything else carries across under its own name.
RENAMED = {"methodology_rationale": "estimator_rationale"}

# Carried deliberately nowhere. See the module docstring.
DROPPED_COLLECTIONS = ("dependencies", "raci_roles")
DROPPED_FIELDS = ("type",)


def _scalars(data: dict) -> dict:
    out = {}
    for key, value in data.items():
        if isinstance(value, list) or value in (None, "") or key == "model_id":
            continue
        target = RENAMED.get(key, key)
        if key in DROPPED_FIELDS or target not in ML_APPLICATION_FIELD_SPECS:
            continue
        out[target] = value
    return out


def _provenance(model_id: str, data: dict) -> dict:
    """The change-history entry that says where this record came from."""
    return {"version": data.get("version") or "", "date": "", "author": "migration",
            "change_type": "Migration",
            "description": f"Migrated from model {model_id}."}


def _versions_as_trains(ml_application_id: str, versions: list, actor: str) -> int:
    """Each recorded version is a fit. Carried oldest first so the sequence reads
    forwards, and the run date is the version's date -- the only date the inventory
    holds for when the thing was actually built."""
    made = 0
    for entry in versions:
        fields = {"fit_id": str(entry.get("version") or f"v{made + 1}")}
        if entry.get("date"):
            fields["run_date"] = entry["date"]
        if entry.get("description"):
            fields["secondary_metrics"] = entry["description"]
        add_collection_item(ml_application_id=ml_application_id,
                            collection=TRAINING_RUNS_COLLECTION, fields=fields,
                            actor=actor, reason="Carried from the model's version history")
        made += 1
    return made


def migrate(model_id: str, ml_application_id: str, estimator: str,
            actor: str = "migration") -> dict:
    model = get_model(model_id)
    if model is None:
        raise SystemExit(f"model {model_id} is not on the inventory")
    if get_ml_application(ml_application_id) is not None:
        raise SystemExit(f"{ml_application_id} already exists")
    data = model["data"] or {}
    fields = _scalars(data)

    # Registration takes the required minimum; everything else is set field by field,
    # so each carries its own event and the trail says what moved.
    minimum = {k: fields.pop(k) for k in
               ("name", "division", "owner", "estimator", "use_case") if k in fields}
    minimum["estimator"] = estimator
    minimum.setdefault("use_case", data.get("description") or f"Migrated from {model_id}.")
    # The source's answered questionnaire is carried below, so the shipped ML set is
    # not seeded on top of it.
    register_ml_application(ml_application_id=ml_application_id, fields=minimum,
                            actor=actor, reason=f"Migrated from {model_id}",
                            seed_questions=not data.get("validation_questions"))
    # A value the source record holds but the target will not accept is REPORTED, not
    # mangled into something acceptable and not allowed to abort the migration. It is
    # nearly always a value that drifted out of its own vocabulary years ago, and
    # quietly rewriting it would hide exactly the fact worth knowing.
    refused = {}
    for key, value in fields.items():
        try:
            update_ml_application_field(ml_application_id=ml_application_id, field=key,
                                        value=value, actor=actor,
                                        reason=f"Carried from {model_id}")
        except DomainError as exc:
            refused[key] = f"{value!r} — {exc}"

    counts = {"fields": len(fields) + len(minimum) - len(refused)}
    if refused:
        counts["NOT CARRIED"] = refused
    for name, items in data.items():
        if not isinstance(items, list) or not items or name in DROPPED_COLLECTIONS:
            continue
        if name == "version_history":
            counts[TRAINING_RUNS_COLLECTION] = _versions_as_trains(
                ml_application_id, items, actor)
            continue
        target = ML_REVIEW_QUESTIONS_COLLECTION if name == "validation_questions" else name
        if target not in ML_APPLICATION_COLLECTION_SPECS:
            # Reported, never dropped in silence: a collection the target cannot hold
            # is information the migration is losing, and the operator has to know.
            # ``documents`` is the exception -- it is not a collection spec at all, and
            # is carried by its own step below. Naming it here cried wolf on the one
            # thing that HAD come across, which teaches an operator to skim the list.
            if name != "documents" and name not in DROPPED_COLLECTIONS:
                counts.setdefault("NOT CARRIED (no home on the record)", []).append(
                    f"{name} ({len(items)})")
            continue
        spec_keys = {f["key"] for f in ML_APPLICATION_COLLECTION_SPECS[target]["fields"]}
        for item in items:
            payload = {k: v for k, v in item.items()
                       if k in spec_keys and v not in (None, "")}
            if payload:
                add_collection_item(ml_application_id=ml_application_id,
                                    collection=target, fields=payload, actor=actor,
                                    reason=f"Carried from {model_id}")
        counts[target] = counts.get(target, 0) + len(items)

    add_collection_item(ml_application_id=ml_application_id, collection="change_history",
                        fields=_provenance(model_id, data), actor=actor,
                        reason="Record the migration")

    # The evidence pack: each file re-filed against the ML Application under the same
    # category, so the dossier the committee saw travels with the record.
    filed = 0
    for doc in list_documents(MODEL_AGGREGATE, model_id):
        path = upload_path(model_scope(model_id), doc["filename"])
        if not path.exists():
            continue
        add_document(aggregate_type=ML_AGGREGATE, aggregate_id=ml_application_id,
                     scope=ml_application_scope(ml_application_id),
                     category=doc.get("category") or "Core Documentation",
                     filename=doc.get("original_name") or doc["filename"],
                     data=path.read_bytes(), description=doc.get("description", ""),
                     actor=actor)
        filed += 1
    counts["documents"] = filed
    rebuild_ml_application_view()
    return counts


def main(argv: list[str]) -> int:
    if len(argv) not in (4, 5):
        print(__doc__)
        return 2
    resolved = DatabaseConfig.from_env().name
    actor = argv[4] if len(argv) == 5 else "migration"
    if resolved in PROTECTED:
        if os.environ.get("MIGRATE_ALLOW_PROTECTED") != resolved:
            print(f"REFUSING: config resolves to '{resolved}', which holds the real "
                  "estate.\nTo write to it deliberately, name it:\n"
                  f"    MIGRATE_ALLOW_PROTECTED={resolved} python -m "
                  "scripts.migrate_model_to_ml_application <model> <id> <estimator> <actor>")
            return 1
        if actor == "migration":
            print("REFUSING: writing to the real estate needs a named author -- an "
                  "event on the live log should say who did it, and 'migration' is "
                  "nobody in the People directory.")
            return 1
        print(f"WRITING TO THE REAL ESTATE: {resolved}, as {actor}")
    print(f"database: {resolved}")
    counts = migrate(argv[1], argv[2], argv[3], actor=actor)
    for key, value in counts.items():
        if isinstance(value, list):
            print(f"  {key}:")
            for entry in value:
                print(f"    {entry}")
            continue
        if key == "NOT CARRIED":
            print("  NOT CARRIED (left on the source record):")
            for field, why in value.items():
                print(f"    {field}: {why}")
            continue
        print(f"  {key:24} {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
