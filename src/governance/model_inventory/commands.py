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
"""Command handlers for the model-inventory aggregate.

Each handler loads the aggregate's event stream, rebuilds its state, validates
the command via the pure decision functions, then appends the resulting event
with optimistic concurrency (``expected_version``). The ``actor`` is recorded on
every event — this is where the SSO-provided identity will be threaded in.
"""
from __future__ import annotations

from typing import Any

from src.database import Event, append_event, read_stream
from src.governance.model_inventory._rules import (
    decide_register,
    decide_retire,
    decide_update_field,
)
from src.governance.model_inventory._state import ModelState, apply, initial_state

AGGREGATE_TYPE = "ModelInventoryEntry"


def _load(model_id: str, config) -> tuple[ModelState, int]:
    events = read_stream(
        aggregate_type=AGGREGATE_TYPE, aggregate_id=model_id, config=config
    )
    state = initial_state()
    for event in events:
        state = apply(state, event.event_type, event.payload)
    return state, len(events)


def _record(
    model_id: str, decision: tuple[str, dict[str, Any]], version: int,
    actor: str, reason: str | None, config,
) -> Event:
    event_type, payload = decision
    return append_event(
        aggregate_type=AGGREGATE_TYPE,
        aggregate_id=model_id,
        event_type=event_type,
        payload=payload,
        actor=actor,
        reason=reason,
        expected_version=version,
        config=config,
    )


def register_model(
    *, model_id: str, name: str, actor: str,
    fields: dict[str, Any] | None = None, reason: str | None = None, config=None,
) -> Event:
    """Register a new model in the inventory."""
    state, version = _load(model_id, config)
    decision = decide_register(state, model_id=model_id, name=name, fields=fields or {})
    return _record(model_id, decision, version, actor, reason, config)


def update_model_field(
    *, model_id: str, field: str, value: Any, actor: str,
    reason: str | None = None, config=None,
) -> Event:
    """Update a single scalar field of an existing model."""
    state, version = _load(model_id, config)
    decision = decide_update_field(state, field=field, value=value)
    return _record(model_id, decision, version, actor, reason, config)


def retire_model(
    *, model_id: str, actor: str, reason: str | None = None, config=None,
) -> Event:
    """Retire a model (it can no longer be edited)."""
    state, version = _load(model_id, config)
    decision = decide_retire(state)
    return _record(model_id, decision, version, actor, reason, config)
