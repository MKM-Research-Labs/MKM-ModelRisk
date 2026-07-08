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
"""Pure decision logic for the model-inventory aggregate.

Each ``decide_*`` function validates a command against the current state and
returns the ``(event_type, payload)`` to append, or raises ``DomainError``.
No I/O happens here, so the rules are trivially unit-testable.
"""
from __future__ import annotations

from typing import Any

from config.governance import (
    COLLECTION_SPECS,
    EDITABLE_FIELDS,
    FIELD_CHOICES,
    TIER_MAX,
    TIER_MIN,
)
from src.governance import collections as coll
from src.governance.errors import DomainError
from src.governance.model_inventory._state import (
    EVENT_FIELD_UPDATED,
    EVENT_REGISTERED,
    EVENT_RETIRED,
    ModelState,
)


def _validate_field(field: str, value: Any) -> None:
    if field == "tier":
        if isinstance(value, bool) or not isinstance(value, int):
            raise DomainError("tier must be an integer")
        if not TIER_MIN <= value <= TIER_MAX:
            raise DomainError(f"tier must be in [{TIER_MIN}, {TIER_MAX}]")
    elif field in FIELD_CHOICES:
        if value not in FIELD_CHOICES[field]:
            allowed = ", ".join(FIELD_CHOICES[field])
            raise DomainError(f"{field} must be one of: {allowed}")


def decide_register(
    state: ModelState, *, model_id: str, name: str, fields: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    if state.exists:
        raise DomainError(f"model {model_id} is already registered")
    if not model_id or not name:
        raise DomainError("model_id and name are required")
    for field, value in fields.items():
        if field not in EDITABLE_FIELDS:
            raise DomainError(f"unknown field: {field}")
        _validate_field(field, value)
    payload: dict[str, Any] = {"model_id": model_id, "name": name}
    payload.update(fields)
    return EVENT_REGISTERED, payload


def decide_update_field(
    state: ModelState, *, field: str, value: Any
) -> tuple[str, dict[str, Any]]:
    if not state.exists:
        raise DomainError("model does not exist")
    if state.retired:
        raise DomainError("cannot edit a retired model")
    if field not in EDITABLE_FIELDS:
        raise DomainError(f"field not editable: {field}")
    _validate_field(field, value)
    return EVENT_FIELD_UPDATED, {"field": field, "value": value}


def decide_retire(state: ModelState) -> tuple[str, dict[str, Any]]:
    if not state.exists:
        raise DomainError("model does not exist")
    if state.retired:
        raise DomainError("model is already retired")
    return EVENT_RETIRED, {}


# --- Structured collections (assumptions, limitations, validation questions, …) ---


def _require_editable(state: ModelState) -> None:
    if not state.exists:
        raise DomainError("model does not exist")
    if state.retired:
        raise DomainError("cannot edit a retired model")


def decide_add_item(
    state: ModelState, *, collection: str, fields: dict[str, Any]
) -> tuple[str, dict[str, Any]]:
    _require_editable(state)
    return coll.decide_add(state.collections, COLLECTION_SPECS, collection=collection, fields=fields)


def decide_update_item(
    state: ModelState, *, collection: str, item_id: str, fields: dict[str, Any]
) -> tuple[str, dict[str, Any]]:
    _require_editable(state)
    return coll.decide_update(
        state.collections, COLLECTION_SPECS, collection=collection, item_id=item_id, fields=fields
    )


def decide_remove_item(
    state: ModelState, *, collection: str, item_id: str
) -> tuple[str, dict[str, Any]]:
    _require_editable(state)
    return coll.decide_remove(
        state.collections, COLLECTION_SPECS, collection=collection, item_id=item_id
    )
