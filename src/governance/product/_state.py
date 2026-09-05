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
# Retirement is hibernation, not deletion: the committee that ratified the retire
# can ratify bringing the record back, so the flag flips both ways and both
# decisions stay in the log.
EVENT_REACTIVATED = "ProductReactivated"


@dataclass(frozen=True)
class ProductState:
    """The reconstructed current state of one Product."""

    exists: bool = False
    retired: bool = False
    fields: dict[str, Any] = field(default_factory=dict)
    collections: dict[str, tuple] = field(default_factory=dict)
    # What ``status`` said before retirement overwrote it with "Retired". A Product
    # is the one aggregate whose retire moves its status field -- the others leave
    # the institution's vocabulary alone -- so bringing one back has to put the word
    # it displaced back. ``None`` for a Product retired before the retire event
    # started recording this; see ``decide_reactivate``.
    status_before_retire: str | None = None


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
        return replace(state, retired=True, fields=updated,
                       status_before_retire=payload.get("from_status"))
    if event_type == EVENT_REACTIVATED:
        updated = dict(state.fields)
        # Only where the retire recorded what it displaced. Otherwise the status is
        # left saying "Retired" on a live Product, which is wrong but visible and
        # editable -- as against quietly inventing a status the committee never saw.
        if payload.get("status"):
            updated["status"] = payload["status"]
        return replace(state, retired=False, fields=updated, status_before_retire=None)
    folded = coll.fold(state.collections, event_type, payload)
    if folded is not None:
        return replace(state, collections=folded)
    return state
