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
"""Pure decision logic for the AI System aggregate (validation only, no I/O).

The risk fields validate against the DIVISION's ratified policy rather than the
static tuples in config, exactly as a model, a Product and an ML Application do: an
AI System's bands are the ones its division's MRC approved, so its categorisation is
challenged on precisely the terms a model's is.

The AI-specific choice fields (hosting, deployment pattern, egress class, oversight
mode, version policy, EU AI Act class) are NOT policy-driven. They are statements of
fact about the system rather than judgements about its risk, and a division cannot
have its own opinion about whether a model is hosted by a third party.
"""
from __future__ import annotations

from typing import Any

from config.governance._ai_system import (AI_SYSTEM_COLLECTION_SPECS,
                                          CONFIGURATION_FIELDS,
                                          AI_SYSTEM_EDITABLE_FIELDS,
                                          AI_SYSTEM_FIELD_CHOICES,
                                          AI_SYSTEM_FIELD_SPECS,
                                          AI_SYSTEM_REGISTER_FIELDS)
from config.governance import FUNCTIONAL_GROUP_FIELD, SIGNOFF_COLLECTIONS
from src.governance import collections as coll
from src.governance.ai_system._state import (EVENT_FIELD_EDITED, EVENT_REACTIVATED,
                                             EVENT_REGISTERED, EVENT_RETIRED,
                                             AISystemState)
from src.governance.errors import DomainError
from src.governance.independence import validate_independence
from src.governance.reference import live_choice_values
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
    elif field in AI_SYSTEM_FIELD_CHOICES:
        # From the admin list where one backs the field, not from the shipped tuple.
        allowed = live_choice_values(AI_SYSTEM_FIELD_SPECS[field])
        if value not in allowed:
            raise DomainError(f"{field} must be one of: {', '.join(allowed)}")


def _require_editable(state: AISystemState) -> None:
    if not state.exists:
        raise DomainError("AI System does not exist")
    if state.retired:
        raise DomainError("AI System is retired")


def decide_register(
    state: AISystemState, *, ai_system_id: str, fields: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    """Register an AI System.

    The register form's minimum is deliberately short (see
    ``AI_SYSTEM_REGISTER_FIELDS``): a record is created before most of it is known,
    and a form demanding the narrative up front is answered with placeholders. What
    is missing afterwards is a completeness finding, which is where somebody acts
    on it.
    """
    if state.exists:
        raise DomainError(f"AI System {ai_system_id} is already registered")
    if not ai_system_id:
        raise DomainError("ai_system_id is required")
    for required in AI_SYSTEM_REGISTER_FIELDS:
        if not fields.get(required):
            raise DomainError(f"{required} is required")
    division = fields.get("division")
    for field, value in fields.items():
        if field not in AI_SYSTEM_FIELD_SPECS:
            raise DomainError(f"unknown field: {field}")
        _validate_field(field, value, division)
        validate_independence(field, value, fields, "AI System")
    # No lifecycle default, for the reason a model and an ML Application set none:
    # the stages are an admin-managed vocabulary and there is no word this code could
    # put here that is certainly in the institution's list.
    payload: dict[str, Any] = {"ai_system_id": ai_system_id}
    payload.update(fields)
    return EVENT_REGISTERED, payload


def decide_edit_field(
    state: AISystemState, *, field: str, value: Any
) -> tuple[str, dict[str, Any]]:
    _require_editable(state)
    if field not in AI_SYSTEM_EDITABLE_FIELDS:
        raise DomainError(f"field not editable: {field}")
    division = value if field == "division" else state.fields.get("division")
    if field == "division":
        reject_division_move_while_grouped(state.fields, value)
    _validate_field(field, value, division)
    validate_independence(field, value, state.fields, "AI System")
    return EVENT_FIELD_EDITED, {"field": field, "value": value}


def decide_retire(state: AISystemState) -> tuple[str, dict[str, Any]]:
    if not state.exists:
        raise DomainError("AI System does not exist")
    if state.retired:
        raise DomainError("AI System is already retired")
    return EVENT_RETIRED, {}


def decide_reactivate(state: AISystemState) -> tuple[str, dict[str, Any]]:
    """Bring a hibernated AI System back into the estate."""
    if not state.exists:
        raise DomainError("AI System does not exist")
    if not state.retired:
        raise DomainError("AI System is not retired")
    return EVENT_REACTIVATED, {}


def _require_signoff_writable(state: AISystemState, collection: str) -> None:
    """A hibernated record is read-only, except to the committee's own machinery.

    Reactivating it has to be requested *on it*, and the decision that hibernated it
    still has to be recordable against it — so the sign-off queue and history stay
    writable while everything else is frozen. A model carries the same exemption for
    the same reason; without it the committee cannot complete the very request it
    just approved.
    """
    if collection in SIGNOFF_COLLECTIONS:
        if not state.exists:
            raise DomainError("AI System does not exist")
        return
    _require_editable(state)


def decide_add_item(
    state: AISystemState, *, collection: str, fields: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    _require_signoff_writable(state, collection)
    return coll.decide_add(state.collections, AI_SYSTEM_COLLECTION_SPECS,
                           collection=collection, fields=fields)


def decide_update_item(
    state: AISystemState, *, collection: str, item_id: str, fields: dict[str, Any]
) -> tuple[str, dict[str, Any]]:
    _require_signoff_writable(state, collection)
    return coll.decide_update(state.collections, AI_SYSTEM_COLLECTION_SPECS,
                              collection=collection, item_id=item_id, fields=fields)


def decide_remove_item(
    state: AISystemState, *, collection: str, item_id: str
) -> tuple[str, dict[str, Any]]:
    _require_editable(state)
    return coll.decide_remove(state.collections, AI_SYSTEM_COLLECTION_SPECS,
                              collection=collection, item_id=item_id)


# The baseline and release decisions live in ``_rules_baseline`` and are re-exported
# here, so every existing import goes on working. Split because this module holds what
# a record IS, and those hold what happens to it over time.
from src.governance.ai_system._rules_baseline import (  # noqa: E402
    decide_record_envelope, decide_seal_manifest, decide_set_threshold,
    decide_take_snapshot, diff_snapshots, manifest_digest, manifest_intact)
