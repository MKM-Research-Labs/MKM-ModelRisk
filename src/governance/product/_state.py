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
"""Current-state fold for the Product aggregate (pure, no I/O)."""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any

from src.governance import collections as coll

EVENT_REGISTERED = "ProductRegistered"
EVENT_REBOUND = "ProductComponentRebound"
EVENT_FIELD_EDITED = "ProductFieldEdited"
EVENT_RETIRED = "ProductRetired"


@dataclass(frozen=True)
class ProductState:
    """The reconstructed current state of one Product."""

    exists: bool = False
    retired: bool = False
    fields: dict[str, Any] = field(default_factory=dict)
    collections: dict[str, tuple] = field(default_factory=dict)


def initial_state() -> ProductState:
    return ProductState()


def apply(state: ProductState, event_type: str, payload: dict[str, Any]) -> ProductState:
    """Fold one event into ``state``. Unknown event types are ignored."""
    if event_type == EVENT_REGISTERED:
        return ProductState(exists=True, retired=False, fields=dict(payload))
    if event_type == EVENT_REBOUND:
        updated = dict(state.fields)
        updated[payload["component"]] = payload["value"]
        return replace(state, fields=updated)
    if event_type == EVENT_FIELD_EDITED:
        updated = dict(state.fields)
        updated[payload["field"]] = payload["value"]
        return replace(state, fields=updated)
    if event_type == EVENT_RETIRED:
        updated = dict(state.fields)
        updated["status"] = "Retired"
        return replace(state, retired=True, fields=updated)
    folded = coll.fold(state.collections, event_type, payload)
    if folded is not None:
        return replace(state, collections=folded)
    return state
