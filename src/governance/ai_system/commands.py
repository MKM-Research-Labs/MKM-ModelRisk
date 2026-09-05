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
"""Command handlers for the AI System aggregate (event-sourced)."""
from __future__ import annotations

from typing import Any

from config.governance import DEFAULT_VQ_STATUS
from config.governance._ai import AI_SYSTEM_QUESTION_LIST, AI_SYSTEM_QUESTIONS
from config.governance._ai_system import (AI_REVIEW_QUESTIONS_COLLECTION,
                                          AI_SYSTEM_COLLECTION_SPECS,
                                          AI_SYSTEM_FIELD_SPECS)
from src.database import Event, append_event, read_stream
from src.governance.ai_system._rules import (decide_add_item, decide_edit_field,
                                             decide_record_envelope,
                                             decide_seal_manifest,
                                             decide_set_threshold,
                                             decide_take_snapshot,
                                             decide_register, decide_remove_item,
                                             decide_retire, decide_update_item)
from src.governance.ai_system._state import AISystemState, apply, initial_state
from src.governance.reference import reject_unknown_values
from src.governance.seeding import compose_questions, seed_items

AGGREGATE_TYPE = "AISystem"


def _load(ai_system_id: str, config) -> tuple[AISystemState, int]:
    events = read_stream(aggregate_type=AGGREGATE_TYPE, aggregate_id=ai_system_id,
                         config=config)
    state = initial_state()
    for event in events:
        state = apply(state, event.event_type, event.payload)
    return state, len(events)


def _record(ai_system_id, decision, version, actor, reason, config) -> Event:
    event_type, payload = decision
    return append_event(
        aggregate_type=AGGREGATE_TYPE, aggregate_id=ai_system_id,
        event_type=event_type, payload=payload, actor=actor, reason=reason,
        expected_version=version, config=config)


def _ai_questions(config) -> list[dict[str, str]]:
    """The questionnaire an AI System is asked: the common questions, then the AI ones.

    Composed rather than read from one list. The five shared questions are asked of any
    application of a model — an ML Application answers the same five — and only what is
    particular to a generative or agentic system lives on the AI list beneath them.
    """
    return compose_questions(AI_SYSTEM_QUESTION_LIST, AI_SYSTEM_QUESTIONS, config)


def _seed_ai_review_questions(ai_system_id, after_version, actor, config) -> None:
    """Copy the AI questionnaire onto the record, immediately after registration."""
    seed_items(
        aggregate_type=AGGREGATE_TYPE, aggregate_id=ai_system_id,
        collection=AI_REVIEW_QUESTIONS_COLLECTION, id_prefix="AIQ",
        items=[{"short_label": q["short_label"], "question": q["question"],
                "status": DEFAULT_VQ_STATUS} for q in _ai_questions(config)],
        after_version=after_version, actor=actor,
        reason="Seed the AI review questions", config=config)


def _check_reference_fields(fields: dict[str, Any], config=None) -> None:
    """Reject a foundation model or provider nobody has defined in Admin.

    Strict for the reason a model's ``type`` is: a record may not name a component
    the institution has never registered. On this record type it matters more than
    usual -- an AI System naming a model nobody approved is exactly the shadow-AI
    case the register exists to surface.

    With one caveat worth stating, because it is the opposite of what "strict"
    suggests: ``reject_unknown_references`` does not enforce an EMPTY list, and the
    foundation-model list ships empty on purpose (see ``_ai.py``). So this field is
    open until an institution curates that list, and closes the moment they add
    their first approved model. That is the right order -- the alternative is a
    register nobody can put a record into on day one -- but it does mean the control
    arrives with the curation rather than with the code.
    """
    from src.governance.reference import reject_unknown_references

    reject_unknown_references(AI_SYSTEM_FIELD_SPECS, fields, config)


def register_ai_system(*, ai_system_id: str, fields: dict[str, Any], actor: str,
                       reason: str = "", seed_questions: bool = True,
                       config=None) -> Event:
    """Register an AI System."""
    _check_reference_fields(fields or {}, config)
    state, version = _load(ai_system_id, config)
    decision = decide_register(state, ai_system_id=ai_system_id, fields=fields)
    event = _record(ai_system_id, decision, version, actor, reason, config)
    if seed_questions:
        _seed_ai_review_questions(ai_system_id, event.stream_seq, actor, config)
    return event


def update_ai_system_field(*, ai_system_id: str, field: str, value: Any, actor: str,
                           reason: str = "", config=None) -> Event:
    _check_reference_fields({field: value}, config)
    state, version = _load(ai_system_id, config)
    decision = decide_edit_field(state, field=field, value=value)
    return _record(ai_system_id, decision, version, actor, reason, config)


def retire_ai_system(*, ai_system_id: str, actor: str, reason: str = "",
                     config=None) -> Event:
    state, version = _load(ai_system_id, config)
    return _record(ai_system_id, decide_retire(state), version, actor, reason, config)


def add_collection_item(*, ai_system_id: str, collection: str, fields: dict[str, Any],
                        actor: str, reason: str = "", config=None) -> Event:
    reject_unknown_values(AI_SYSTEM_COLLECTION_SPECS, collection, fields, config)
    state, version = _load(ai_system_id, config)
    decision = decide_add_item(state, collection=collection, fields=fields)
    return _record(ai_system_id, decision, version, actor, reason, config)


def update_collection_item(*, ai_system_id: str, collection: str, item_id: str,
                           fields: dict[str, Any], actor: str, reason: str = "",
                           config=None) -> Event:
    reject_unknown_values(AI_SYSTEM_COLLECTION_SPECS, collection, fields, config)
    state, version = _load(ai_system_id, config)
    decision = decide_update_item(state, collection=collection, item_id=item_id,
                                  fields=fields)
    return _record(ai_system_id, decision, version, actor, reason, config)


def remove_collection_item(*, ai_system_id: str, collection: str, item_id: str,
                           actor: str, reason: str = "", config=None) -> Event:
    state, version = _load(ai_system_id, config)
    decision = decide_remove_item(state, collection=collection, item_id=item_id)
    return _record(ai_system_id, decision, version, actor, reason, config)


def take_configuration_snapshot(*, ai_system_id: str, actor: str, reason: str = "",
                                taken_at: str | None = None, config=None) -> Event:
    """Record the system's configuration as it stands now, as a new immutable version."""
    from datetime import datetime, timezone
    stamped = taken_at or datetime.now(timezone.utc).isoformat(timespec="seconds")
    state, version = _load(ai_system_id, config)
    decision = decide_take_snapshot(state, taken_at=stamped)
    return _record(ai_system_id, decision, version, actor, reason, config)


def record_variability_envelope(*, ai_system_id: str, scores, actor: str,
                                reason: str = "", note: str = "",
                                measured_at: str | None = None, config=None) -> Event:
    """Record the envelope N runs under the current configuration showed."""
    from datetime import datetime, timezone
    stamped = measured_at or datetime.now(timezone.utc).isoformat(timespec="seconds")
    state, version = _load(ai_system_id, config)
    decision = decide_record_envelope(state, scores=scores, measured_at=stamped,
                                      note=note)
    return _record(ai_system_id, decision, version, actor, reason, config)


def set_trigger_threshold(*, ai_system_id: str, property_name: str, threshold,
                          fallback: str, rationale: str = "", actor: str,
                          reason: str = "", set_at: str | None = None,
                          config=None) -> Event:
    """Set the bar for one property, and what happens when it is breached."""
    from datetime import datetime, timezone
    stamped = set_at or datetime.now(timezone.utc).isoformat(timespec="seconds")
    state, version = _load(ai_system_id, config)
    decision = decide_set_threshold(state, property_name=property_name,
                                    threshold=threshold, fallback=fallback,
                                    rationale=rationale, set_at=stamped)
    return _record(ai_system_id, decision, version, actor, reason, config)


def seal_release_manifest(*, ai_system_id: str, release: str, change_class: str,
                          actor: str, reason: str = "", note: str = "",
                          sealed_at: str | None = None, config=None) -> Event:
    """Seal an immutable record of what this release contained."""
    from datetime import datetime, timezone
    stamped = sealed_at or datetime.now(timezone.utc).isoformat(timespec="seconds")
    state, version = _load(ai_system_id, config)
    decision = decide_seal_manifest(state, release=release, change_class=change_class,
                                    sealed_at=stamped, note=note)
    return _record(ai_system_id, decision, version, actor, reason, config)
