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
"""Current-state fold for the PVM aggregate (pure, no I/O)."""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any

from src.governance import collections as coll

EVENT_REGISTERED = "PvmRegistered"
EVENT_REBOUND = "PvmComponentRebound"
EVENT_FIELD_EDITED = "PvmFieldEdited"
EVENT_RETIRED = "PvmRetired"


@dataclass(frozen=True)
class PvmState:
    """The reconstructed current state of one PVM."""

    exists: bool = False
    retired: bool = False
    fields: dict[str, Any] = field(default_factory=dict)
    collections: dict[str, tuple] = field(default_factory=dict)


def initial_state() -> PvmState:
    return PvmState()


def apply(state: PvmState, event_type: str, payload: dict[str, Any]) -> PvmState:
    """Fold one event into ``state``. Unknown event types are ignored."""
    if event_type == EVENT_REGISTERED:
        return PvmState(exists=True, retired=False, fields=dict(payload))
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
