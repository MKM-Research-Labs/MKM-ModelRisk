# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
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

from config.governance import DEFAULT_VQ_STATUS, SR262_QUESTIONS
from src.database import Event, append_event, read_stream
from src.governance import collections as coll
from src.governance.model_inventory._rules import (
    decide_add_item,
    decide_register,
    decide_remove_item,
    decide_retire,
    decide_update_field,
    decide_update_item,
)
from src.governance.model_inventory._state import ModelState, apply, initial_state

AGGREGATE_TYPE = "ModelInventoryEntry"


def _seed_validation_questions(model_id, after_version, actor, config) -> None:
    """Append the nine SR 26-2 questions immediately after registration."""
    version = after_version
    for index, question in enumerate(SR262_QUESTIONS, start=1):
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
            reason="Seed SR 26-2 validation questions", expected_version=version,
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


def register_model(
    *, model_id: str, name: str, actor: str,
    fields: dict[str, Any] | None = None, reason: str | None = None,
    require_company: bool = False, config=None,
) -> Event:
    """Register a new model, then seed its SR 26-2 validation questions."""
    state, version = _load(model_id, config)
    decision = decide_register(
        state, model_id=model_id, name=name, fields=fields or {},
        require_company=require_company,
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
    decision = decide_update_field(state, field=field, value=value)
    return _record(model_id, decision, version, actor, reason, config)


def retire_model(
    *, model_id: str, actor: str, reason: str | None = None, config=None,
) -> Event:
    """Retire a model (it can no longer be edited)."""
    state, version = _load(model_id, config)
    decision = decide_retire(state)
    return _record(model_id, decision, version, actor, reason, config)


def add_collection_item(
    *, model_id: str, collection: str, fields: dict[str, Any], actor: str,
    reason: str | None = None, config=None,
) -> Event:
    """Add an item to a structured collection (assumptions, limitations, …)."""
    state, version = _load(model_id, config)
    decision = decide_add_item(state, collection=collection, fields=fields)
    return _record(model_id, decision, version, actor, reason, config)


def update_collection_item(
    *, model_id: str, collection: str, item_id: str, fields: dict[str, Any],
    actor: str, reason: str | None = None, config=None,
) -> Event:
    """Update fields of an existing collection item."""
    state, version = _load(model_id, config)
    decision = decide_update_item(
        state, collection=collection, item_id=item_id, fields=fields
    )
    return _record(model_id, decision, version, actor, reason, config)


def remove_collection_item(
    *, model_id: str, collection: str, item_id: str, actor: str,
    reason: str | None = None, config=None,
) -> Event:
    """Remove an item from a structured collection."""
    state, version = _load(model_id, config)
    decision = decide_remove_item(state, collection=collection, item_id=item_id)
    return _record(model_id, decision, version, actor, reason, config)
