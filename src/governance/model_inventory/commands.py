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
"""Command handlers for the model-inventory aggregate.

Each handler loads the aggregate's event stream, rebuilds its state, validates
the command via the pure decision functions, then appends the resulting event
with optimistic concurrency (``expected_version``). The ``actor`` is recorded on
every event — this is where the SSO-provided identity will be threaded in.
"""
from __future__ import annotations

from typing import Any

from config.governance import (COLLECTION_SPECS, DEFAULT_VQ_STATUS,
                               DEPENDENCIES_COLLECTION, MODEL_FIELD_SPECS,
                               REFERENCE_SPECS, REVIEW_QUESTION_LIST,
                               SR262_QUESTIONS)
from src.database import Event, append_event, read_stream
from src.governance import collections as coll
from src.governance.errors import DomainError
from src.governance.graph import has_cycle, self_loops
from src.governance.model_inventory._rules import (
    decide_add_item,
    decide_reactivate,
    decide_register,
    decide_remove_item,
    decide_retire,
    decide_update_field,
    decide_update_item,
)
from src.governance.model_inventory._state import ModelState, apply, initial_state

AGGREGATE_TYPE = "ModelInventoryEntry"


def _review_questions(config) -> list[dict]:
    """The questionnaire a newly registered model is asked.

    The institution's own list (Admin > Review), falling back to the SR 26-2 set
    only where none has been recorded — a fresh database before the first-run seed,
    or one whose list has been emptied. A model is asked the questions that stood
    when it was registered; editing the list afterwards does not rewrite the
    answers already given, which is why each model keeps its own copy.
    """
    from src.governance.reference import get_reference_lists
    try:
        recorded = get_reference_lists(config=config).get(REVIEW_QUESTION_LIST) or []
    except Exception:
        recorded = []
    asked = [{"short_label": q.get("short_label") or "", "question": q.get("question") or ""}
             for q in recorded if (q.get("question") or "").strip()]
    return asked or [dict(q) for q in SR262_QUESTIONS]


def _seed_validation_questions(model_id, after_version, actor, config) -> None:
    """Copy the review questionnaire onto the model, immediately after registration."""
    version = after_version
    for index, question in enumerate(_review_questions(config), start=1):
        payload = {
            "collection": "validation_questions",
            "item_id": f"VQ-{index:03d}",
            "short_label": question["short_label"],
            "question": question["question"],
            "status": DEFAULT_VQ_STATUS,
        }
        append_event(
            aggregate_type=AGGREGATE_TYPE, aggregate_id=model_id,
            event_type=coll.EVENT_ITEM_ADDED, payload=payload, actor=actor,
            reason="Seed the review questions", expected_version=version,
            config=config,
        )
        version += 1


def _load(model_id: str, config) -> tuple[ModelState, int]:
    events = read_stream(
        aggregate_type=AGGREGATE_TYPE, aggregate_id=model_id, config=config
    )
    state = initial_state()
    for event in events:
        state = apply(state, event.event_type, event.payload)
    return state, len(events)


def _record(
    model_id: str, decision: tuple[str, dict[str, Any]], version: int,
    actor: str, reason: str | None, config,
) -> Event:
    event_type, payload = decision
    return append_event(
        aggregate_type=AGGREGATE_TYPE,
        aggregate_id=model_id,
        event_type=event_type,
        payload=payload,
        actor=actor,
        reason=reason,
        expected_version=version,
        config=config,
    )


def _reject_unknown_references(
    specs: dict[str, dict[str, Any]], fields: dict[str, Any], config=None,
) -> None:
    """Reject a value not on the admin list for any ``strict_reference`` field.

    Lives here rather than in ``_rules`` because the allowed values are rows in
    the reference store, and the rules stay pure. ``specs`` maps a field key to
    its spec; only fields flagged strict are checked — see MODEL_FIELD_SPECS for
    why the others are deliberately open.

    An empty list is not enforced: on a fresh database, before the defaults are
    seeded, there is nothing to validate against and rejecting everything would
    make the field unusable rather than safe.
    """
    from src.governance.reference import get_reference_lists

    strict = {key: spec["reference"] for key, spec in specs.items()
              if spec.get("strict_reference") and key in fields
              and str(fields[key] or "").strip()}
    if not strict:
        return
    lists = get_reference_lists(config)
    for key, list_name in strict.items():
        spec = REFERENCE_SPECS[list_name]
        allowed = [item.get(spec.get("display", "value"))
                   for item in lists.get(list_name, ())]
        if allowed and fields[key] not in allowed:
            raise DomainError(
                f"{key} must be one of: {', '.join(str(a) for a in allowed)}")


def _check_reference_fields(fields: dict[str, Any], config=None) -> None:
    """Strict-reference guard for a model's scalar fields (e.g. type, vendor)."""
    _reject_unknown_references(MODEL_FIELD_SPECS, fields, config)


def _check_collection_reference_fields(
    collection: str, fields: dict[str, Any], config=None,
) -> None:
    """Strict-reference guard for a collection item's fields (e.g. a
    ``data_sources`` item's data_source picked from the admin list)."""
    spec = COLLECTION_SPECS.get(collection)
    if not spec:
        return
    by_key = {field["key"]: field for field in spec["fields"]}
    _reject_unknown_references(by_key, fields, config)


def register_model(
    *, model_id: str, name: str, actor: str,
    fields: dict[str, Any] | None = None, reason: str | None = None,
    config=None,
) -> Event:
    """Register a new model, then seed its SR 26-2 validation questions."""
    state, version = _load(model_id, config)
    _check_reference_fields(fields or {}, config)
    decision = decide_register(
        state, model_id=model_id, name=name, fields=fields or {},
    )
    event = _record(model_id, decision, version, actor, reason, config)
    _seed_validation_questions(model_id, event.stream_seq, actor, config)
    return event


def update_model_field(
    *, model_id: str, field: str, value: Any, actor: str,
    reason: str | None = None, config=None,
) -> Event:
    """Update a single scalar field of an existing model."""
    state, version = _load(model_id, config)
    _check_reference_fields({field: value}, config)
    decision = decide_update_field(state, field=field, value=value)
    return _record(model_id, decision, version, actor, reason, config)


def retire_model(
    *, model_id: str, actor: str, reason: str | None = None, config=None,
) -> Event:
    """Retire (hibernate) a model — it drops out of the active inventory and can
    no longer be edited. Ratified by the MRC, so this runs off an approved
    request rather than straight from the owner."""
    state, version = _load(model_id, config)
    decision = decide_retire(state)
    return _record(model_id, decision, version, actor, reason, config)


def reactivate_model(
    *, model_id: str, actor: str, reason: str | None = None, config=None,
) -> Event:
    """Bring a hibernated model back into the active inventory. Ratified by the
    MRC on the same footing as the retire that put it there."""
    state, version = _load(model_id, config)
    decision = decide_reactivate(state)
    return _record(model_id, decision, version, actor, reason, config)


def _guard_dependency(model_id: str, new_state: ModelState, config) -> None:
    """Cross-model invariants for a declared dependency — a cross-aggregate check
    the pure rules cannot see. The related model must exist, a model may not depend
    on itself, and the edge must not close a cycle in the whole derived chain."""
    # Imported here (not at module load) because the derivation reads the
    # inventory projection, which imports this module — a top-level import would
    # be circular.
    from src.governance.model_inventory.chain import edges_for_model
    from src.governance.model_inventory.projection import get_model, list_models

    items = new_state.collections.get(DEPENDENCIES_COLLECTION, ())
    for item in items:
        related = item.get("model_id")
        if related and get_model(related, config=config) is None:
            raise DomainError(f"unknown related model: {related}")
    this_edges = edges_for_model(model_id, items)
    if self_loops(this_edges):
        raise DomainError("a model cannot depend on itself")
    other_edges = [
        edge
        # The cycle guard reasons about the declared graph, which a hibernated
        # model is still part of: a cycle hidden while it sleeps would come
        # back the moment it was reactivated.
        for other in list_models(config=config, include_retired=True)
        if other["model_id"] != model_id
        for edge in edges_for_model(
            other["model_id"],
            other.get("data", {}).get(DEPENDENCIES_COLLECTION, []) or [],
        )
    ]
    if has_cycle(this_edges + other_edges):
        raise DomainError("declaring this dependency would create a cycle in the model chain")


def _guard_if_dependency(
    model_id: str, state: ModelState, decision: tuple[str, dict[str, Any]],
    collection: str, config,
) -> None:
    if collection == DEPENDENCIES_COLLECTION:
        _guard_dependency(model_id, apply(state, decision[0], decision[1]), config)


def add_collection_item(
    *, model_id: str, collection: str, fields: dict[str, Any], actor: str,
    reason: str | None = None, config=None,
) -> Event:
    """Add an item to a structured collection (assumptions, limitations, …)."""
    state, version = _load(model_id, config)
    _check_collection_reference_fields(collection, fields, config)
    decision = decide_add_item(state, collection=collection, fields=fields)
    _guard_if_dependency(model_id, state, decision, collection, config)
    return _record(model_id, decision, version, actor, reason, config)


def update_collection_item(
    *, model_id: str, collection: str, item_id: str, fields: dict[str, Any],
    actor: str, reason: str | None = None, config=None,
) -> Event:
    """Update fields of an existing collection item."""
    state, version = _load(model_id, config)
    _check_collection_reference_fields(collection, fields, config)
    decision = decide_update_item(
        state, collection=collection, item_id=item_id, fields=fields
    )
    _guard_if_dependency(model_id, state, decision, collection, config)
    return _record(model_id, decision, version, actor, reason, config)


def remove_collection_item(
    *, model_id: str, collection: str, item_id: str, actor: str,
    reason: str | None = None, config=None,
) -> Event:
    """Remove an item from a structured collection."""
    state, version = _load(model_id, config)
    decision = decide_remove_item(state, collection=collection, item_id=item_id)
    return _record(model_id, decision, version, actor, reason, config)
