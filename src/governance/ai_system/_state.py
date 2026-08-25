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
"""Current-state fold for the AI System aggregate (pure, no I/O).

The event names are the one thing here that cannot be changed later: the log is
append-only, so a rename would leave every existing event unreadable by the fold.
Named for the concept rather than for whatever a screen currently calls it -- the
ML Application's display label moved once already and its event names did not have
to move with it.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any

from src.governance import collections as coll

EVENT_REGISTERED = "AISystemRegistered"
EVENT_FIELD_EDITED = "AISystemFieldEdited"
EVENT_RETIRED = "AISystemRetired"


@dataclass(frozen=True)
class AISystemState:
    """The reconstructed current state of one AI System."""

    exists: bool = False
    retired: bool = False
    fields: dict[str, Any] = field(default_factory=dict)
    collections: dict[str, tuple] = field(default_factory=dict)


def initial_state() -> AISystemState:
    return AISystemState()


def record_data(state: AISystemState) -> dict[str, Any]:
    """A state as the flat record shape everything downstream reads."""
    data = dict(state.fields)
    for collection, items in state.collections.items():
        data[collection] = list(items)
    return data


def apply(state: AISystemState, event_type: str,
          payload: dict[str, Any]) -> AISystemState:
    """Fold one event into ``state``. Unknown event types are ignored."""
    if event_type == EVENT_REGISTERED:
        return AISystemState(exists=True, retired=False, fields=dict(payload))
    if event_type == EVENT_FIELD_EDITED:
        updated = dict(state.fields)
        updated[payload["field"]] = payload["value"]
        return replace(state, fields=updated)
    if event_type == EVENT_RETIRED:
        # ``retired`` is the fact; the lifecycle stage is the institution's own
        # vocabulary and is not overwritten with a word we chose.
        return replace(state, retired=True)
    folded = coll.fold(state.collections, event_type, payload)
    if folded is not None:
        return replace(state, collections=folded)
    return state


__all__ = ["AISystemState", "initial_state", "record_data", "apply",
           "EVENT_REGISTERED", "EVENT_FIELD_EDITED", "EVENT_RETIRED"]
