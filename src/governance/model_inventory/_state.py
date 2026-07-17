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
"""Current-state fold for the model-inventory aggregate (pure, no I/O).

``apply`` folds one event into the running state; replaying a stream from
``initial_state`` reconstructs the model's current state for command validation
and for building the read-model projection.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any

from src.governance import collections as coll

EVENT_REGISTERED = "ModelRegistered"
EVENT_FIELD_UPDATED = "ModelFieldUpdated"
EVENT_RETIRED = "ModelRetired"
# Retirement is hibernation, not deletion: a retired model drops out of the
# active inventory but the committee can bring it back, so the flag flips both
# ways and the history of both decisions stays in the log.
EVENT_REACTIVATED = "ModelReactivated"


@dataclass(frozen=True)
class ModelState:
    """The reconstructed current state of one model inventory entry."""

    exists: bool = False
    retired: bool = False
    fields: dict[str, Any] = field(default_factory=dict)
    # collection name -> tuple of item dicts (each carrying its item_id)
    collections: dict[str, tuple] = field(default_factory=dict)


def initial_state() -> ModelState:
    """The empty state of a model that has no events yet."""
    return ModelState()


def apply(state: ModelState, event_type: str, payload: dict[str, Any]) -> ModelState:
    """Fold one event into ``state``. Unknown event types are ignored."""
    if event_type == EVENT_REGISTERED:
        return ModelState(exists=True, retired=False, fields=dict(payload))
    if event_type == EVENT_FIELD_UPDATED:
        updated = dict(state.fields)
        updated[payload["field"]] = payload["value"]
        return replace(state, fields=updated)
    if event_type == EVENT_RETIRED:
        return replace(state, retired=True)
    if event_type == EVENT_REACTIVATED:
        return replace(state, retired=False)
    folded = coll.fold(state.collections, event_type, payload)
    if folded is not None:
        return replace(state, collections=folded)
    return state
