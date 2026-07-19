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
"""Pure decision functions for the model-handoff aggregate.

Each returns the ``(event_type, payload)`` to append, or raises ``DomainError``.
Cross-aggregate invariants — that both endpoints exist and the edge is actually
declared in the chain — cannot be seen from one aggregate's state, so they live in
the command layer, not here.
"""
from __future__ import annotations

from typing import Any

from config.governance import COLLECTION_SPECS
from src.governance import collections as coll
from src.governance.errors import DomainError
from src.governance.model_handoff._state import (
    EVENT_DECLARED,
    EVENT_FIELD_UPDATED,
    HandoffState,
)

STATUS_DRAFT = "Draft"
# The prose fields an owner edits directly. ``compatibility`` is a single free-text
# note for now; Phase B.2 expands it into the structured compatibility analysis.
EDITABLE_FIELDS = ("data_handoff", "compatibility")


def decide_declare(
    state: HandoffState, *, from_model: str, to_model: str
) -> tuple[str, dict[str, Any]]:
    if state.exists:
        raise DomainError("a handoff is already declared for this edge")
    if not from_model or not to_model:
        raise DomainError("from_model and to_model are required")
    if from_model == to_model:
        raise DomainError("a handoff cannot loop a model to itself")
    return EVENT_DECLARED, {
        "from_model": from_model, "to_model": to_model,
        "data_handoff": "", "compatibility": "", "status": STATUS_DRAFT,
    }


def decide_update_field(
    state: HandoffState, *, field: str, value: Any
) -> tuple[str, dict[str, Any]]:
    if not state.exists:
        raise DomainError("handoff does not exist")
    if field not in EDITABLE_FIELDS:
        raise DomainError(f"field not editable: {field}")
    return EVENT_FIELD_UPDATED, {"field": field, "value": value}


def decide_add_item(
    state: HandoffState, *, collection: str, fields: dict[str, Any]
) -> tuple[str, dict[str, Any]]:
    if not state.exists:
        raise DomainError("handoff does not exist")
    return coll.decide_add(state.collections, COLLECTION_SPECS, collection=collection, fields=fields)


def decide_update_item(
    state: HandoffState, *, collection: str, item_id: str, fields: dict[str, Any]
) -> tuple[str, dict[str, Any]]:
    if not state.exists:
        raise DomainError("handoff does not exist")
    return coll.decide_update(
        state.collections, COLLECTION_SPECS, collection=collection, item_id=item_id, fields=fields
    )


def decide_remove_item(
    state: HandoffState, *, collection: str, item_id: str
) -> tuple[str, dict[str, Any]]:
    if not state.exists:
        raise DomainError("handoff does not exist")
    return coll.decide_remove(
        state.collections, COLLECTION_SPECS, collection=collection, item_id=item_id
    )
