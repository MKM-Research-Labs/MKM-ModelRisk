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
"""Current-state fold for the ML Application aggregate (pure, no I/O).

The event names are the one thing here that cannot be changed later: the log is
append-only, so a rename would leave every existing event unreadable by the fold.
They are therefore named for the concept and not for whatever a screen currently
calls it -- the display label has already moved once (ML-Instance -> ML
Application) and these did not have to move with it.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any

from src.governance import collections as coll
from src.governance.model_class import with_model_class

EVENT_REGISTERED = "MLApplicationRegistered"
EVENT_FIELD_EDITED = "MLApplicationFieldEdited"
EVENT_RETIRED = "MLApplicationRetired"
# Retirement is hibernation, not deletion: the committee that ratified the retire
# can ratify bringing the record back, so the flag flips both ways and both
# decisions stay in the log.
EVENT_REACTIVATED = "MLApplicationReactivated"


@dataclass(frozen=True)
class MLApplicationState:
    """The reconstructed current state of one ML Application."""

    exists: bool = False
    retired: bool = False
    fields: dict[str, Any] = field(default_factory=dict)
    collections: dict[str, tuple] = field(default_factory=dict)


def initial_state() -> MLApplicationState:
    return MLApplicationState()


def record_data(state: MLApplicationState) -> dict[str, Any]:
    """A state as the flat record shape everything downstream reads.

    Shared by the read model and by the completion gate: the gate has to ask the same
    question of the same shape the screens do, and a second copy of this fold is a
    second chance for the two to disagree about what a record contains.
    """
    data = with_model_class("MLApplication", dict(state.fields))
    for collection, items in state.collections.items():
        data[collection] = list(items)
    return data


def apply(state: MLApplicationState, event_type: str,
          payload: dict[str, Any]) -> MLApplicationState:
    """Fold one event into ``state``. Unknown event types are ignored."""
    if event_type == EVENT_REGISTERED:
        return MLApplicationState(exists=True, retired=False, fields=dict(payload))
    if event_type == EVENT_FIELD_EDITED:
        updated = dict(state.fields)
        updated[payload["field"]] = payload["value"]
        return replace(state, fields=updated)
    if event_type == EVENT_RETIRED:
        # ``retired`` is the fact; the lifecycle stage is the institution's own
        # vocabulary and is not overwritten with a word we chose. A model retires the
        # same way, and its screens read the flag rather than a stage.
        return replace(state, retired=True)
    if event_type == EVENT_REACTIVATED:
        return replace(state, retired=False)
    folded = coll.fold(state.collections, event_type, payload)
    if folded is not None:
        return replace(state, collections=folded)
    return state
