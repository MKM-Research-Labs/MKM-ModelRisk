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
"""Current-state fold for the model-inventory aggregate (pure, no I/O).

``apply`` folds one event into the running state; replaying a stream from
``initial_state`` reconstructs the model's current state for command validation
and for building the read-model projection.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any

EVENT_REGISTERED = "ModelRegistered"
EVENT_FIELD_UPDATED = "ModelFieldUpdated"
EVENT_RETIRED = "ModelRetired"


@dataclass(frozen=True)
class ModelState:
    """The reconstructed current state of one model inventory entry."""

    exists: bool = False
    retired: bool = False
    fields: dict[str, Any] = field(default_factory=dict)


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
    return state
