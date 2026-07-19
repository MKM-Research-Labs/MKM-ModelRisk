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
"""Current-state fold for a model-to-model handoff (pure, no I/O).

One aggregate per directed chain edge (producer -> consumer). It carries scalar
fields (the two endpoints, a prose summary, a compatibility note, a status) plus
structured collections — the field lineage now, and the sign-off queue once the
handoff goes to the committee. Modelled like the inventory entry so the same
generic collection machinery and the sign-off Subject adapter both apply.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any

from src.governance import collections as coll

EVENT_DECLARED = "HandoffDeclared"
EVENT_FIELD_UPDATED = "HandoffFieldUpdated"


@dataclass(frozen=True)
class HandoffState:
    """The current state of one handoff: scalar fields plus its collections."""

    exists: bool = False
    fields: dict[str, Any] = field(default_factory=dict)
    collections: dict[str, tuple] = field(default_factory=dict)


def initial_state() -> HandoffState:
    return HandoffState()


def apply(state: HandoffState, event_type: str, payload: dict[str, Any]) -> HandoffState:
    """Fold one event into ``state``. Unknown event types are ignored."""
    if event_type == EVENT_DECLARED:
        return HandoffState(exists=True, fields=dict(payload))
    if event_type == EVENT_FIELD_UPDATED:
        updated = dict(state.fields)
        updated[payload["field"]] = payload["value"]
        return replace(state, fields=updated)
    folded = coll.fold(state.collections, event_type, payload)
    if folded is not None:
        return replace(state, collections=folded)
    return state
