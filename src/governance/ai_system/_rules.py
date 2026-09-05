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
from src.governance import collections as coll
from src.governance.ai_system._state import (EVENT_FIELD_EDITED, EVENT_REGISTERED,
                                             EVENT_RETIRED,
                                             EVENT_ENVELOPE_RECORDED,
                                             EVENT_SNAPSHOT_TAKEN, AISystemState)
from src.governance.errors import DomainError
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
    elif field in AI_SYSTEM_FIELD_CHOICES and value not in AI_SYSTEM_FIELD_CHOICES[field]:
        allowed = ", ".join(AI_SYSTEM_FIELD_CHOICES[field])
        raise DomainError(f"{field} must be one of: {allowed}")


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
    _validate_field(field, value, division)
    return EVENT_FIELD_EDITED, {"field": field, "value": value}


def decide_retire(state: AISystemState) -> tuple[str, dict[str, Any]]:
    if not state.exists:
        raise DomainError("AI System does not exist")
    if state.retired:
        raise DomainError("AI System is already retired")
    return EVENT_RETIRED, {}


def decide_add_item(
    state: AISystemState, *, collection: str, fields: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    _require_editable(state)
    return coll.decide_add(state.collections, AI_SYSTEM_COLLECTION_SPECS,
                           collection=collection, fields=fields)


def decide_update_item(
    state: AISystemState, *, collection: str, item_id: str, fields: dict[str, Any]
) -> tuple[str, dict[str, Any]]:
    _require_editable(state)
    return coll.decide_update(state.collections, AI_SYSTEM_COLLECTION_SPECS,
                              collection=collection, item_id=item_id, fields=fields)


def decide_remove_item(
    state: AISystemState, *, collection: str, item_id: str
) -> tuple[str, dict[str, Any]]:
    _require_editable(state)
    return coll.decide_remove(state.collections, AI_SYSTEM_COLLECTION_SPECS,
                              collection=collection, item_id=item_id)


def decide_take_snapshot(
    state: AISystemState, *, taken_at: str
) -> tuple[str, dict[str, Any]]:
    """Record the configuration as it stands, as a numbered, immutable version.

    Takes the values from the RECORD rather than from the caller. A snapshot the caller
    supplied the contents of would be a claim about the configuration; this is a reading
    of it, and the two differ exactly when it matters.

    An unchanged configuration is still refused a new version. Two identical snapshots
    a month apart say the configuration did not move, which the absence of a snapshot
    says just as well and without inviting "which of these two is current".
    """
    _require_editable(state)
    values = {field: state.fields.get(field) for field in CONFIGURATION_FIELDS}
    if state.snapshots and state.snapshots[-1].get("values") == values:
        raise DomainError("the configuration has not changed since the last snapshot")
    return EVENT_SNAPSHOT_TAKEN, {
        "config_version": len(state.snapshots) + 1,
        "values": values,
        "taken_at": taken_at,
    }


def diff_snapshots(before: dict[str, Any], after: dict[str, Any]) -> list[dict[str, Any]]:
    """What moved between two snapshots, field by field.

    Pure, and over the SNAPSHOTS rather than over the record: comparing a snapshot with
    the record's current values would answer a different question ("has it moved since")
    and the two get confused precisely when somebody is trying to explain a change.
    """
    old, new = before.get("values") or {}, after.get("values") or {}
    return [{"field": field, "before": old.get(field), "after": new.get(field)}
            for field in sorted(set(old) | set(new))
            if old.get(field) != new.get(field)]


def decide_record_envelope(
    state: AISystemState, *, scores, measured_at: str, note: str = "",
) -> tuple[str, dict[str, Any]]:
    """Record what N runs under the current configuration showed.

    Refuses where the runs do not support an envelope, rather than recording a narrow
    one — see ``compute_envelope``. The refusal is a DomainError because recording an
    unsupported envelope is not a lesser reading, it is a wrong one.

    Bound to the configuration in force, which is the latest snapshot. A system with no
    snapshot cannot have an envelope: there would be nothing to say what it was measured
    under, and the envelope would outlive any change silently.
    """
    from config.governance._ai_baseline import ENVELOPE_OK
    from src.governance.ai_system.envelope import compute_envelope

    _require_editable(state)
    if not state.snapshots:
        raise DomainError("take a configuration snapshot first: an envelope has to say "
                          "which configuration it was measured under")
    config_version = state.snapshots[-1].get("config_version")
    envelope = compute_envelope(scores, config_version=config_version)
    if envelope["status"] != ENVELOPE_OK:
        raise DomainError(envelope["detail"])
    return EVENT_ENVELOPE_RECORDED, {**envelope, "measured_at": measured_at,
                                     "note": note}
