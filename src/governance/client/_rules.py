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
"""Pure decision logic for the Client aggregate (validation only, no I/O)."""
from __future__ import annotations

from typing import Any

from config.governance import (
    CLIENT_COLLECTION_SPECS,
    CLIENT_EDITABLE_FIELDS,
    CLIENT_FIELD_CHOICES,
    CLIENT_FIELD_SPECS,
)
from src.governance import collections as coll
from src.governance.errors import DomainError
from src.governance.client._state import (
    EVENT_FIELD_EDITED,
    EVENT_REGISTERED,
    EVENT_RETIRED,
    ClientState,
)


def _validate_field(field: str, value: Any) -> None:
    if field in CLIENT_FIELD_CHOICES and value not in CLIENT_FIELD_CHOICES[field]:
        allowed = ", ".join(CLIENT_FIELD_CHOICES[field])
        raise DomainError(f"{field} must be one of: {allowed}")


def _require_editable(state: ClientState) -> None:
    if not state.exists:
        raise DomainError("Client does not exist")
    if state.retired:
        raise DomainError("cannot edit a retired Client")


def decide_register(
    state: ClientState, *, client_id: str, name: str, fields: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    """Register a Client. Only the company name is required at registration."""
    if state.exists:
        raise DomainError(f"Client {client_id} is already registered")
    if not name:
        raise DomainError("name is required")
    for field, value in fields.items():
        if field not in CLIENT_FIELD_SPECS:
            raise DomainError(f"unknown field: {field}")
        _validate_field(field, value)
    payload: dict[str, Any] = {"client_id": client_id, "name": name, "status": "Active"}
    payload.update(fields)
    return EVENT_REGISTERED, payload


def decide_edit_field(
    state: ClientState, *, field: str, value: Any,
) -> tuple[str, dict[str, Any]]:
    _require_editable(state)
    if field not in CLIENT_EDITABLE_FIELDS:
        raise DomainError(f"field not editable: {field}")
    _validate_field(field, value)
    return EVENT_FIELD_EDITED, {"field": field, "value": value}


def decide_retire(state: ClientState) -> tuple[str, dict[str, Any]]:
    if not state.exists:
        raise DomainError("Client does not exist")
    if state.retired:
        raise DomainError("Client is already retired")
    return EVENT_RETIRED, {}


def decide_add_item(
    state: ClientState, *, collection: str, fields: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    _require_editable(state)
    return coll.decide_add(
        state.collections, CLIENT_COLLECTION_SPECS, collection=collection, fields=fields)


def decide_update_item(
    state: ClientState, *, collection: str, item_id: str, fields: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    _require_editable(state)
    return coll.decide_update(
        state.collections, CLIENT_COLLECTION_SPECS, collection=collection,
        item_id=item_id, fields=fields)


def decide_remove_item(
    state: ClientState, *, collection: str, item_id: str,
) -> tuple[str, dict[str, Any]]:
    _require_editable(state)
    return coll.decide_remove(
        state.collections, CLIENT_COLLECTION_SPECS, collection=collection, item_id=item_id)
