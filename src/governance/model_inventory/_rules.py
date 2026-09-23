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
"""Decision logic for the model-inventory aggregate.

Each ``decide_*`` function validates a command against the current state and
returns the ``(event_type, payload)`` to append, or raises ``DomainError``.

Nothing is WRITTEN here, so a rule can be exercised on a state object alone. Reads
are another matter: a vocabulary an institution owns cannot be checked without
looking it up, so the risk fields ask the division's ratified policy, a functional
group asks its ratified list, and a reference-backed choice asks the admin list.
This docstring claimed no I/O at all long after the first of those arrived.
"""
from __future__ import annotations

from typing import Any

from config.governance import (
    APPEND_ONLY_COLLECTIONS,
    COLLECTION_SPECS,
    EDITABLE_FIELDS,
    FIELD_CHOICES,
    FUNCTIONAL_GROUP_FIELD,
    LIFECYCLE_STAGE_FIELD,
    MODEL_FIELD_SPECS,
    SIGNOFF_COLLECTIONS,
)
from src.governance import collections as coll
from src.governance.model_class import reject_immutable_edit, stamp_model_class
from src.governance.errors import DomainError
from src.governance.independence import validate_independence
from src.governance.reference import live_choice_values
from src.governance.model_inventory._state import (
    EVENT_FIELD_UPDATED,
    EVENT_REACTIVATED,
    EVENT_REGISTERED,
    EVENT_RETIRED,
    ModelState,
)
from src.governance.functional_groups import (reject_division_move_while_grouped,
                                              reject_unknown_functional_group)
from src.governance.lifecycle_stages import (reject_division_move_out_of_stage,
                                             reject_unknown_lifecycle_stage)
from src.governance.risk_policy import get_risk_policy

# Risk fields whose allowed values come from the DIVISION's live policy, not a global
# constant: the bands of a dimension, or the overall risk-rating names.
_POLICY_CHOICE_FIELDS = {
    "materiality": lambda policy: [b["name"] for b in policy["dimensions"]["materiality"]["bands"]],
    "complexity": lambda policy: [b["name"] for b in policy["dimensions"]["complexity"]["bands"]],
    "rag_rating": lambda policy: [b["name"] for b in policy["risk_ratings"]],
}


def _validate_field(field: str, value: Any, division: Any) -> None:
    """Validate one field.

    Risk fields (tier == Mission Criticality, materiality, complexity, rag_rating) are
    checked against the model's DIVISION risk policy, and ``functional_group`` against
    that division's separately-ratified group list; everything else against the global
    choice sets."""
    if field == "tier":
        if isinstance(value, bool) or not isinstance(value, int):
            raise DomainError("tier must be an integer")
        # Mission-Criticality band scores are the valid tier values for this division.
        bands = get_risk_policy(division or "")["dimensions"]["mission_criticality"]["bands"]
        scores = [b["score"] for b in bands]
        if value not in scores:
            allowed = ", ".join(str(s) for s in sorted(scores))
            raise DomainError(f"tier must be one of: {allowed}")
    elif field in _POLICY_CHOICE_FIELDS:
        allowed = _POLICY_CHOICE_FIELDS[field](get_risk_policy(division or ""))
        if value not in allowed:
            raise DomainError(f"{field} must be one of: {', '.join(allowed)}")
    elif field == FUNCTIONAL_GROUP_FIELD:
        reject_unknown_functional_group(value, division)
    elif field == LIFECYCLE_STAGE_FIELD:
        # Checked BEFORE the choice branch, as the functional group is: the field is
        # still a ``choice`` in the specs (its static options are the fallback the
        # console shows before the registry loads), but what it may actually hold is
        # the division's ratified list, not the tuple beside the spec.
        reject_unknown_lifecycle_stage(value, division)
    elif field in FIELD_CHOICES:
        # The vocabulary as the admin list stands, not as it shipped: a field backed by
        # a reference is offered from that list on every screen, so it has to be
        # accepted from it here (see ``live_choice_values``).
        allowed = live_choice_values(MODEL_FIELD_SPECS[field])
        if value not in allowed:
            raise DomainError(f"{field} must be one of: {', '.join(allowed)}")


def decide_register(
    state: ModelState, *, model_id: str, name: str, fields: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    if state.exists:
        raise DomainError(f"model {model_id} is already registered")
    if not model_id or not name:
        raise DomainError("model_id and name are required")
    # Risk fields are validated against this model's division policy — set in the same
    # command at registration.
    # Inside SR 26-2 scope by what it is; stamped rather than asked.
    fields = stamp_model_class("ModelInventoryEntry", fields)
    division = fields.get("division")
    for field, value in fields.items():
        if field not in EDITABLE_FIELDS:
            raise DomainError(f"unknown field: {field}")
        _validate_field(field, value, division)
        validate_independence(field, value, fields, "model")
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
    reject_immutable_edit(MODEL_FIELD_SPECS, field)
    # Editing division itself changes which policy governs the risk fields; otherwise
    # use the model's current division.
    division = value if field == "division" else state.fields.get("division")
    if field == "division":
        reject_division_move_while_grouped(state.fields, value)
        reject_division_move_out_of_stage(state.fields, value)
    _validate_field(field, value, division)
    validate_independence(field, value, state.fields, "model")
    # Capture the prior value so the audit trail can show old -> new. Older
    # events predate this and simply have no "from" (rendered as blank).
    return EVENT_FIELD_UPDATED, {
        "field": field, "value": value, "from": state.fields.get(field),
    }


def decide_retire(state: ModelState) -> tuple[str, dict[str, Any]]:
    if not state.exists:
        raise DomainError("model does not exist")
    if state.retired:
        raise DomainError("model is already retired")
    return EVENT_RETIRED, {}


def decide_reactivate(state: ModelState) -> tuple[str, dict[str, Any]]:
    """Bring a hibernated model back into the active inventory."""
    if not state.exists:
        raise DomainError("model does not exist")
    if not state.retired:
        raise DomainError("model is not retired")
    return EVENT_REACTIVATED, {}


# --- Structured collections (assumptions, limitations, validation questions, …) ---


def _require_editable(state: ModelState) -> None:
    if not state.exists:
        raise DomainError("model does not exist")
    if state.retired:
        raise DomainError("cannot edit a retired model")


def decide_add_item(
    state: ModelState, *, collection: str, fields: dict[str, Any]
) -> tuple[str, dict[str, Any]]:
    # A hibernated model is read-only, except to the committee's own machinery
    # (see SIGNOFF_COLLECTIONS): reactivating it has to be requested *on it*, and
    # the decision that hibernated it still has to be recordable against it.
    if collection in SIGNOFF_COLLECTIONS:
        if not state.exists:
            raise DomainError("model does not exist")
    else:
        _require_editable(state)
    return coll.decide_add(state.collections, COLLECTION_SPECS, collection=collection, fields=fields)


def _require_amendable(collection: str) -> None:
    """Refuse to change or remove a row in an append-only collection.

    The review notes are the record of how a model was challenged, and they are
    printed in the report the committee receives. A challenge that could be edited
    or deleted afterwards is not evidence of anything — so the rule lives here, in
    the domain, rather than resting on the console not offering the button. A
    correction is a new note, as it would be in minutes.
    """
    if collection in APPEND_ONLY_COLLECTIONS:
        raise DomainError(
            f"{collection} is append-only: a note cannot be edited or removed, "
            "only answered by another note"
        )


def decide_update_item(
    state: ModelState, *, collection: str, item_id: str, fields: dict[str, Any]
) -> tuple[str, dict[str, Any]]:
    # Same exemption as adding: a hibernated model's reactivate request still has
    # to be walked through the queue (Pending -> Attached -> Completed), which is
    # an update on the retired model itself.
    _require_amendable(collection)
    if collection in SIGNOFF_COLLECTIONS:
        if not state.exists:
            raise DomainError("model does not exist")
    else:
        _require_editable(state)
    return coll.decide_update(
        state.collections, COLLECTION_SPECS, collection=collection, item_id=item_id, fields=fields
    )


def decide_remove_item(
    state: ModelState, *, collection: str, item_id: str
) -> tuple[str, dict[str, Any]]:
    _require_amendable(collection)
    _require_editable(state)
    return coll.decide_remove(
        state.collections, COLLECTION_SPECS, collection=collection, item_id=item_id
    )
