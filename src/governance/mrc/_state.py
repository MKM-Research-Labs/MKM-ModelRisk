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
"""Current-state fold for the MRC-meeting aggregate (pure, no I/O).

Scalar meeting fields plus structured collections (agenda, decisions, actions,
participants, minutes, models in scope) folded via the shared collection engine.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any

from src.governance import collections as coll

EVENT_SCHEDULED = "MeetingScheduled"
EVENT_FIELD_UPDATED = "MeetingFieldUpdated"


@dataclass(frozen=True)
class MeetingState:
    """Reconstructed current state of one MRC meeting."""

    exists: bool = False
    fields: dict[str, Any] = field(default_factory=dict)
    collections: dict[str, tuple] = field(default_factory=dict)


def initial_state() -> MeetingState:
    return MeetingState()


def apply(state: MeetingState, event_type: str, payload: dict[str, Any]) -> MeetingState:
    """Fold one event into ``state``. Unknown event types are ignored."""
    if event_type == EVENT_SCHEDULED:
        return MeetingState(exists=True, fields=dict(payload))
    if event_type == EVENT_FIELD_UPDATED:
        fields = dict(state.fields)
        fields[payload["field"]] = payload["value"]
        return replace(state, fields=fields)
    folded = coll.fold(state.collections, event_type, payload)
    if folded is not None:
        return replace(state, collections=folded)
    return state
