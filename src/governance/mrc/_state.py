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
"""Current-state fold for the MRC-meeting aggregate (pure, no I/O)."""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any

EVENT_SCHEDULED = "MeetingScheduled"
EVENT_FIELD_UPDATED = "MeetingFieldUpdated"
EVENT_AGENDA_ADDED = "AgendaItemAdded"
EVENT_DECISION_LOGGED = "DecisionLogged"
EVENT_ACTION_RAISED = "ActionRaised"
EVENT_ACTION_STATUS_SET = "ActionStatusSet"


@dataclass(frozen=True)
class MeetingState:
    """Reconstructed current state of one MRC meeting."""

    exists: bool = False
    fields: dict[str, Any] = field(default_factory=dict)
    agenda: tuple = ()
    decisions: tuple = ()
    actions: tuple = ()


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
    if event_type == EVENT_AGENDA_ADDED:
        return replace(state, agenda=state.agenda + (payload,))
    if event_type == EVENT_DECISION_LOGGED:
        return replace(state, decisions=state.decisions + (payload,))
    if event_type == EVENT_ACTION_RAISED:
        return replace(state, actions=state.actions + (payload,))
    if event_type == EVENT_ACTION_STATUS_SET:
        actions = tuple(
            {**a, "status": payload["status"]}
            if a["action_id"] == payload["action_id"]
            else a
            for a in state.actions
        )
        return replace(state, actions=actions)
    return state
