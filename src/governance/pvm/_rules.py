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
"""Pure decision logic for the PVM aggregate (validation only, no I/O).

Cross-aggregate facts (does the Analytics Model resolve to a live model; would
the component combination duplicate an existing PVM) are computed by the command
layer and passed in, so these functions stay pure and unit-testable.
"""
from __future__ import annotations

from typing import Any

from config.governance import (
    PVM_BINDINGS,
    PVM_COLLECTION_SPECS,
    PVM_EDITABLE_FIELDS,
    PVM_FIELD_CHOICES,
    PVM_FIELD_SPECS,
)
from src.governance import collections as coll
from src.governance.errors import DomainError
from src.governance.pvm._state import (
    EVENT_FIELD_EDITED,
    EVENT_REBOUND,
    EVENT_REGISTERED,
    EVENT_RETIRED,
    PvmState,
)


def _validate_field(field: str, value: Any) -> None:
    if field in PVM_FIELD_CHOICES and value not in PVM_FIELD_CHOICES[field]:
        allowed = ", ".join(PVM_FIELD_CHOICES[field])
        raise DomainError(f"{field} must be one of: {allowed}")


def _require_editable(state: PvmState) -> None:
    if not state.exists:
        raise DomainError("PVM does not exist")
    if state.retired:
        raise DomainError("cannot edit a retired PVM")


def decide_register(
    state: PvmState, *, pvm_id: str, product: str, fields: dict[str, Any],
    analytics_live: bool, duplicate: bool,
) -> tuple[str, dict[str, Any]]:
    if state.exists:
        raise DomainError(f"PVM {pvm_id} is already registered")
    if not pvm_id or not product:
        raise DomainError("pvm_id and product are required")
    for binding in PVM_BINDINGS:
        if not fields.get(binding):
            raise DomainError(f"{binding} is required")
    if not analytics_live:
        raise DomainError("analytics_model must reference a live inventory model")
    if duplicate:
        raise DomainError("a PVM already binds this Product + Analytics + Market Data + Agent")
    for field, value in fields.items():
        if field not in PVM_FIELD_SPECS:
            raise DomainError(f"unknown field: {field}")
        _validate_field(field, value)
    payload: dict[str, Any] = {"pvm_id": pvm_id, "product": product, "status": "Proposed"}
    payload.update(fields)
    return EVENT_REGISTERED, payload


def decide_rebind(
    state: PvmState, *, component: str, value: str, analytics_live: bool, duplicate: bool,
) -> tuple[str, dict[str, Any]]:
    _require_editable(state)
    if component not in PVM_BINDINGS:
        raise DomainError(f"not a component binding: {component}")
    if not value:
        raise DomainError(f"{component} is required")
    if component == "analytics_model" and not analytics_live:
        raise DomainError("analytics_model must reference a live inventory model")
    if duplicate:
        raise DomainError("rebinding would duplicate an existing PVM's component combination")
    return EVENT_REBOUND, {"component": component, "value": value}


def decide_edit_field(
    state: PvmState, *, field: str, value: Any
) -> tuple[str, dict[str, Any]]:
    _require_editable(state)
    if field not in PVM_EDITABLE_FIELDS:
        raise DomainError(f"field not editable: {field}")
    _validate_field(field, value)
    return EVENT_FIELD_EDITED, {"field": field, "value": value}


def decide_retire(state: PvmState) -> tuple[str, dict[str, Any]]:
    if not state.exists:
        raise DomainError("PVM does not exist")
    if state.retired:
        raise DomainError("PVM is already retired")
    return EVENT_RETIRED, {}


def decide_add_item(
    state: PvmState, *, collection: str, fields: dict[str, Any]
) -> tuple[str, dict[str, Any]]:
    _require_editable(state)
    return coll.decide_add(
        state.collections, PVM_COLLECTION_SPECS, collection=collection, fields=fields)


def decide_update_item(
    state: PvmState, *, collection: str, item_id: str, fields: dict[str, Any]
) -> tuple[str, dict[str, Any]]:
    _require_editable(state)
    return coll.decide_update(
        state.collections, PVM_COLLECTION_SPECS, collection=collection, item_id=item_id, fields=fields)


def decide_remove_item(
    state: PvmState, *, collection: str, item_id: str
) -> tuple[str, dict[str, Any]]:
    _require_editable(state)
    return coll.decide_remove(
        state.collections, PVM_COLLECTION_SPECS, collection=collection, item_id=item_id)
