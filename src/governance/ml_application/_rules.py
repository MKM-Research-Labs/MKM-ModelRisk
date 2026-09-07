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
"""Pure decision logic for the ML Application aggregate (validation only, no I/O).

The risk fields validate against the DIVISION's ratified policy rather than the
static tuples in config, exactly as a model and a Product do. That is decision 8
-- the same risk classification -- made real: an ML Application's bands are the
ones its division's MRC approved, so its categorisation can be challenged on
precisely the terms a model's can.
"""
from __future__ import annotations

from typing import Any

from config.governance import (FUNCTIONAL_GROUP_FIELD,
                               ML_APPLICATION_COLLECTION_SPECS,
                               ML_APPLICATION_EDITABLE_FIELDS,
                               ML_APPLICATION_FIELD_CHOICES,
                               ML_APPLICATION_FIELD_SPECS,
                               ML_APPLICATION_REGISTER_FIELDS,
                               SIGNOFF_COLLECTIONS)
from src.governance import collections as coll
from src.governance.errors import DomainError
from src.governance.independence import validate_independence
from src.governance.ml_application._state import (EVENT_FIELD_EDITED, EVENT_REACTIVATED,
                                                  EVENT_REGISTERED, EVENT_RETIRED,
                                                  MLApplicationState)
from src.governance.functional_groups import (reject_division_move_while_grouped,
                                              reject_unknown_functional_group)
from src.governance.risk_policy import get_risk_policy

# Risk fields whose allowed values come from the record's DIVISION policy.
_POLICY_CHOICE_FIELDS = {
    "materiality": lambda policy: [b["name"] for b in policy["dimensions"]["materiality"]["bands"]],
    "complexity": lambda policy: [b["name"] for b in policy["dimensions"]["complexity"]["bands"]],
    "rag_rating": lambda policy: [b["name"] for b in policy["risk_ratings"]],
}


def _validate_field(field: str, value: Any, division: Any) -> None:
    if field in _POLICY_CHOICE_FIELDS:
        allowed = _POLICY_CHOICE_FIELDS[field](get_risk_policy(division or ""))
        if value not in allowed:
            raise DomainError(f"{field} must be one of: {', '.join(allowed)}")
    elif field == FUNCTIONAL_GROUP_FIELD:
        reject_unknown_functional_group(value, division)
    elif field in ML_APPLICATION_FIELD_CHOICES and value not in ML_APPLICATION_FIELD_CHOICES[field]:
        allowed = ", ".join(ML_APPLICATION_FIELD_CHOICES[field])
        raise DomainError(f"{field} must be one of: {allowed}")


def _require_editable(state: MLApplicationState) -> None:
    if not state.exists:
        raise DomainError("ML Application does not exist")
    if state.retired:
        raise DomainError("cannot edit a retired ML Application")


def decide_register(
    state: MLApplicationState, *, ml_application_id: str, fields: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    """Register an ML Application.

    The register form's minimum is deliberately short (see
    ``ML_APPLICATION_REGISTER_FIELDS``): a record is created before most of it is
    known, and a form demanding the narrative up front is answered with
    placeholders. What is missing afterwards is a completeness finding, which is
    where that gap belongs and where somebody actually acts on it.
    """
    if state.exists:
        raise DomainError(f"ML Application {ml_application_id} is already registered")
    if not ml_application_id:
        raise DomainError("ml_application_id is required")
    for required in ML_APPLICATION_REGISTER_FIELDS:
        if not fields.get(required):
            raise DomainError(f"{required} is required")
    division = fields.get("division")
    for field, value in fields.items():
        if field not in ML_APPLICATION_FIELD_SPECS:
            raise DomainError(f"unknown field: {field}")
        _validate_field(field, value, division)
        validate_independence(field, value, fields, "ML Application")
    # No lifecycle default. The stages are an admin-managed vocabulary the institution
    # sets (Admin > Vocabulary), so there is no word this code could put here that is
    # certainly in their list -- a model sets none at registration for the same reason.
    payload: dict[str, Any] = {"ml_application_id": ml_application_id}
    payload.update(fields)
    return EVENT_REGISTERED, payload


def decide_edit_field(
    state: MLApplicationState, *, field: str, value: Any
) -> tuple[str, dict[str, Any]]:
    _require_editable(state)
    if field not in ML_APPLICATION_EDITABLE_FIELDS:
        raise DomainError(f"field not editable: {field}")
    division = value if field == "division" else state.fields.get("division")
    if field == "division":
        reject_division_move_while_grouped(state.fields, value)
    _validate_field(field, value, division)
    validate_independence(field, value, state.fields, "ML Application")
    return EVENT_FIELD_EDITED, {"field": field, "value": value}


def decide_retire(state: MLApplicationState) -> tuple[str, dict[str, Any]]:
    if not state.exists:
        raise DomainError("ML Application does not exist")
    if state.retired:
        raise DomainError("ML Application is already retired")
    return EVENT_RETIRED, {}


def decide_reactivate(state: MLApplicationState) -> tuple[str, dict[str, Any]]:
    """Bring a hibernated ML Application back into the estate."""
    if not state.exists:
        raise DomainError("ML Application does not exist")
    if not state.retired:
        raise DomainError("ML Application is not retired")
    return EVENT_REACTIVATED, {}


def _require_signoff_writable(state: MLApplicationState, collection: str) -> None:
    """A hibernated record is read-only, except to the committee's own machinery.

    Reactivating it has to be requested *on it*, and the decision that hibernated it
    still has to be recordable against it — so the sign-off queue and history stay
    writable while everything else is frozen. A model carries the same exemption for
    the same reason; without it the committee cannot complete the very request it
    just approved.
    """
    if collection in SIGNOFF_COLLECTIONS:
        if not state.exists:
            raise DomainError("ML Application does not exist")
        return
    _require_editable(state)


def decide_add_item(
    state: MLApplicationState, *, collection: str, fields: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    _require_signoff_writable(state, collection)
    return coll.decide_add(state.collections, ML_APPLICATION_COLLECTION_SPECS,
                           collection=collection, fields=fields)


def decide_update_item(
    state: MLApplicationState, *, collection: str, item_id: str, fields: dict[str, Any]
) -> tuple[str, dict[str, Any]]:
    _require_signoff_writable(state, collection)
    return coll.decide_update(state.collections, ML_APPLICATION_COLLECTION_SPECS,
                              collection=collection, item_id=item_id, fields=fields)


def decide_remove_item(
    state: MLApplicationState, *, collection: str, item_id: str
) -> tuple[str, dict[str, Any]]:
    _require_editable(state)
    return coll.decide_remove(state.collections, ML_APPLICATION_COLLECTION_SPECS,
                              collection=collection, item_id=item_id)
