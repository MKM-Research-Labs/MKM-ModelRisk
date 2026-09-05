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
"""Command handlers for the ML Application aggregate (event-sourced)."""
from __future__ import annotations

from typing import Any

from config.governance import (DEFAULT_VQ_STATUS,
                               ML_APPLICATION_COLLECTION_SPECS,
                               ML_APPLICATION_FIELD_SPECS,
                               ML_APPLICATION_QUESTIONS,
                               ML_APPLICATION_QUESTION_LIST,
                               ML_REVIEW_QUESTIONS_COLLECTION)
from src.database import Event, append_event, read_stream
from src.governance import collections as coll
from src.governance.ml_application._state import record_data
from src.governance.ml_application.review_scope import (COMPLETING_REVIEW_STATUS, REVIEW_STATUS_FIELD, guard_review_complete)
from src.governance.ml_application._rules import (decide_add_item, decide_edit_field,
                                                  decide_register, decide_remove_item,
                                                  decide_retire, decide_update_item)
from src.governance.ml_application._state import MLApplicationState, apply, initial_state
from src.governance.reference import reject_unknown_values
from src.governance.seeding import compose_questions, seed_items

AGGREGATE_TYPE = "MLApplication"


def _load(ml_application_id: str, config) -> tuple[MLApplicationState, int]:
    events = read_stream(aggregate_type=AGGREGATE_TYPE, aggregate_id=ml_application_id,
                         config=config)
    state = initial_state()
    for event in events:
        state = apply(state, event.event_type, event.payload)
    return state, len(events)


def _record(ml_application_id, decision, version, actor, reason, config) -> Event:
    event_type, payload = decision
    return append_event(
        aggregate_type=AGGREGATE_TYPE, aggregate_id=ml_application_id,
        event_type=event_type, payload=payload, actor=actor, reason=reason,
        expected_version=version, config=config)


def _ml_questions(config) -> list[dict[str, str]]:
    """The questionnaire an ML Application is asked: the common questions, then the ML
    ones.

    Composed rather than read from one list. The five shared questions are asked of any
    application of a model — an AI System answers the same five — and only what is
    particular to a fitted estimator lives on the ML list beneath them.
    """
    return compose_questions(ML_APPLICATION_QUESTION_LIST, ML_APPLICATION_QUESTIONS,
                             config)

def _seed_ml_review_questions(ml_application_id, after_version, actor, config) -> None:
    """Copy the ML questionnaire onto the record, immediately after registration."""
    seed_items(
        aggregate_type=AGGREGATE_TYPE, aggregate_id=ml_application_id,
        collection=ML_REVIEW_QUESTIONS_COLLECTION, id_prefix="MLQ",
        items=[{"short_label": q["short_label"], "question": q["question"],
                "status": DEFAULT_VQ_STATUS} for q in _ml_questions(config)],
        after_version=after_version, actor=actor,
        reason="Seed the ML review questions", config=config)


def _check_reference_fields(fields: dict[str, Any], config=None) -> None:
    """Reject an estimator nobody has defined in Admin.

    ``estimator`` is strict for the same reason a model's ``type`` is: a record may
    not name a component the institution has never registered. Enforced here rather
    than in ``_rules`` because the allowed values are rows in the reference store
    and the rules stay pure.
    """
    from src.governance.reference import reject_unknown_references

    reject_unknown_references(ML_APPLICATION_FIELD_SPECS, fields, config)


def register_ml_application(*, ml_application_id: str, fields: dict[str, Any],
                            actor: str, reason: str = "", seed_questions: bool = True,
                            config=None) -> Event:
    """Register an ML Application.

    ``seed_questions`` is false only for a record migrating in from the inventory with
    a questionnaire it has already answered. Seeding on top of that would leave the
    record carrying two sets -- the ten it has not been asked and the nine it has --
    and a reader cannot tell which the committee saw.
    """
    _check_reference_fields(fields or {}, config)
    state, version = _load(ml_application_id, config)
    decision = decide_register(state, ml_application_id=ml_application_id, fields=fields)
    event = _record(ml_application_id, decision, version, actor, reason, config)
    if seed_questions:
        _seed_ml_review_questions(ml_application_id, event.stream_seq, actor, config)
    return event


def update_ml_application_field(*, ml_application_id: str, field: str, value: Any,
                                actor: str, reason: str = "", config=None) -> Event:
    _check_reference_fields({field: value}, config)
    state, version = _load(ml_application_id, config)
    # Declaring the review complete is the one edit the policy gates. It needs a read
    # (the division's ratified policy), so it cannot live in the pure rules -- the same
    # reason the model inventory guards its dependency graph from here.
    if field == REVIEW_STATUS_FIELD and value == COMPLETING_REVIEW_STATUS:
        guard_review_complete(record_data(state), "Signing off this review", config)
    decision = decide_edit_field(state, field=field, value=value)
    return _record(ml_application_id, decision, version, actor, reason, config)


def retire_ml_application(*, ml_application_id: str, actor: str, reason: str = "",
                          config=None) -> Event:
    state, version = _load(ml_application_id, config)
    return _record(ml_application_id, decide_retire(state), version, actor, reason, config)


def add_collection_item(*, ml_application_id: str, collection: str, fields: dict[str, Any],
                        actor: str, reason: str = "", config=None) -> Event:
    reject_unknown_values(ML_APPLICATION_COLLECTION_SPECS, collection, fields, config)
    state, version = _load(ml_application_id, config)
    decision = decide_add_item(state, collection=collection, fields=fields)
    return _record(ml_application_id, decision, version, actor, reason, config)


def update_collection_item(*, ml_application_id: str, collection: str, item_id: str,
                           fields: dict[str, Any], actor: str, reason: str = "",
                           config=None) -> Event:
    reject_unknown_values(ML_APPLICATION_COLLECTION_SPECS, collection, fields, config)
    state, version = _load(ml_application_id, config)
    decision = decide_update_item(state, collection=collection, item_id=item_id, fields=fields)
    return _record(ml_application_id, decision, version, actor, reason, config)


def remove_collection_item(*, ml_application_id: str, collection: str, item_id: str,
                           actor: str, reason: str = "", config=None) -> Event:
    state, version = _load(ml_application_id, config)
    decision = decide_remove_item(state, collection=collection, item_id=item_id)
    return _record(ml_application_id, decision, version, actor, reason, config)
