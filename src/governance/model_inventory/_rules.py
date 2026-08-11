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
"""Pure decision logic for the model-inventory aggregate.

Each ``decide_*`` function validates a command against the current state and
returns the ``(event_type, payload)`` to append, or raises ``DomainError``.
No I/O happens here, so the rules are trivially unit-testable.
"""
from __future__ import annotations

from typing import Any

from config.governance import (
    APPEND_ONLY_COLLECTIONS,
    COLLECTION_SPECS,
    EDITABLE_FIELDS,
    FIELD_CHOICES,
    SIGNOFF_COLLECTIONS,
)
from config.permissions import ENFORCE_REVIEWER_INDEPENDENCE
from src.governance import collections as coll
from src.governance.errors import DomainError
from src.identity import same_person
from src.governance.model_inventory._state import (
    EVENT_FIELD_UPDATED,
    EVENT_REACTIVATED,
    EVENT_REGISTERED,
    EVENT_RETIRED,
    ModelState,
)
from src.governance.risk_policy import get_risk_policy

# Risk fields whose allowed values come from the DIVISION's live policy, not a global
# constant: the bands of a dimension, or the overall risk-rating names.
_POLICY_CHOICE_FIELDS = {
    "materiality": lambda policy: [b["name"] for b in policy["dimensions"]["materiality"]["bands"]],
    "complexity": lambda policy: [b["name"] for b in policy["dimensions"]["complexity"]["bands"]],
    "rag_rating": lambda policy: [b["name"] for b in policy["risk_ratings"]],
}


def _validate_field(field: str, value: Any, division: Any) -> None:
    """Validate one field. Risk fields (tier == Mission Criticality, materiality,
    complexity, rag_rating) are checked against the model's DIVISION policy; everything
    else against the global choice sets."""
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
    elif field in FIELD_CHOICES:
        if value not in FIELD_CHOICES[field]:
            allowed = ", ".join(FIELD_CHOICES[field])
            raise DomainError(f"{field} must be one of: {allowed}")


# The two fields the segregation-of-duties rule holds apart, each named against the
# other so a write to either is checked from the same table.
_INDEPENDENT_OF = {"peer_reviewer": "owner", "owner": "peer_reviewer"}


def _validate_independence(field: str, value: Any, held: dict[str, Any]) -> None:
    """Refuse a write that would make a model's reviewer its own owner.

    Checked on both fields rather than only on ``peer_reviewer``: a model with a
    distinct reviewer can be put in breach just as easily by moving the ownership
    onto them, and a rule enforced on one side of a pair is not enforced.

    Only the write that creates the breach is refused. A record already in breach
    stays editable in every other respect -- the audit reports it, and locking the
    record would leave the owner unable to correct anything else about it.
    """
    if ENFORCE_REVIEWER_INDEPENDENCE == "never" or field not in _INDEPENDENT_OF:
        return
    counterpart = held.get(_INDEPENDENT_OF[field])
    if same_person(value, counterpart):
        raise DomainError(
            f"{field} must not be the model's own owner: a review by the owner is "
            f"not an independent one. Name somebody other than {counterpart}.")


def decide_register(
    state: ModelState, *, model_id: str, name: str, fields: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    if state.exists:
        raise DomainError(f"model {model_id} is already registered")
    if not model_id or not name:
        raise DomainError("model_id and name are required")
    # Risk fields are validated against this model's division policy — set in the same
    # command at registration.
    division = fields.get("division")
    for field, value in fields.items():
        if field not in EDITABLE_FIELDS:
            raise DomainError(f"unknown field: {field}")
        _validate_field(field, value, division)
        _validate_independence(field, value, fields)
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
    # Editing division itself changes which policy governs the risk fields; otherwise
    # use the model's current division.
    division = value if field == "division" else state.fields.get("division")
    _validate_field(field, value, division)
    _validate_independence(field, value, state.fields)
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
