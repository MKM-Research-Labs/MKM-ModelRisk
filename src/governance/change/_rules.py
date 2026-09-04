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
"""Pure decision logic for the Change aggregate: the four-tier classification engine.

``classify`` is the engine. It is a total function of (fields before, fields after,
affected artifacts, record type) against ``CHANGE_TRIGGERS`` -- no clock, no database,
no randomness -- so the same proposal classifies the same way every time it is asked,
which is the property the whole thing rests on. A tier that moved between two readings
of the same proposal would make the register unusable as evidence.

Not a literal tier name, depth or field list in this module (R1): everything it reasons
about comes from ``config/governance/_change.py``.
"""
from __future__ import annotations

from typing import Any, Iterable

from config.governance._change import (CHANGE_CLASSES, CHANGE_TRIGGERS,
                                       DEFAULT_CHANGE_CLASS, revalidation_depth_for,
                                       workflow_for)
from src.governance.change._state import (EVENT_CLASSIFIED, EVENT_PROPOSED,
                                          EVENT_SUPERSEDED, ChangeState)
from src.governance.errors import DomainError


def _severity(change_class: str) -> int:
    """Position in the ascending ``CHANGE_CLASSES`` tuple."""
    return CHANGE_CLASSES.index(change_class)


def _rule_applies(rule: dict[str, Any], subject_type: str) -> bool:
    applies_to = rule.get("applies_to") or ()
    return not applies_to or subject_type in applies_to


def _class_for(subject_type: str, *, field: str = "", artifact: str = "") -> str:
    """The tier one moved field or artifact triggers. First matching rule wins."""
    for rule in CHANGE_TRIGGERS:
        if not _rule_applies(rule, subject_type):
            continue
        if field and field in (rule.get("fields") or ()):
            return rule["change_class"]
        if artifact and artifact in (rule.get("artifacts") or ()):
            return rule["change_class"]
    return DEFAULT_CHANGE_CLASS


def moved_fields(before: dict[str, Any], after: dict[str, Any]) -> tuple[str, ...]:
    """The fields ``after`` actually moves, in a stable order.

    Only keys present in ``after`` are considered: a proposal describes the movement it
    intends, so a field absent from ``after`` is one it does not touch rather than one
    it clears. Comparison is by value, so restating a field at its current value is not
    a change and cannot inflate a proposal's tier.
    """
    return tuple(key for key in sorted(after) if after[key] != before.get(key))


def classify(*, subject_type: str, before: dict[str, Any], after: dict[str, Any],
             affected_artifacts: Iterable[str] = ()) -> str:
    """The tier a proposed change falls into: the most severe any one part triggers.

    Most severe rather than first or last, because a change is a single decision and
    its cost is set by its worst part -- a proposal that renames a model *and* swaps
    its methodology is a methodology swap with a rename attached.
    """
    triggered = [_class_for(subject_type, field=name)
                 for name in moved_fields(before, after)]
    triggered += [_class_for(subject_type, artifact=name)
                  for name in (affected_artifacts or ())]
    if not triggered:
        return DEFAULT_CHANGE_CLASS
    return max(triggered, key=_severity)


def _require_open(state: ChangeState) -> None:
    if not state.exists:
        raise DomainError("Change does not exist")
    if state.superseded:
        raise DomainError("Change is superseded")


def decide_propose(
    state: ChangeState, *, change_id: str, subject_type: str, subject_id: str,
    rationale: str, before: dict[str, Any], after: dict[str, Any],
    affected_artifacts: Iterable[str] = (),
) -> tuple[str, dict[str, Any]]:
    """Propose a change against one record.

    The proposal is not classified here. Classification is a separate act with its own
    event so the register can show a tier that somebody recorded on a date, against the
    triggers that stood then -- rather than one this code recomputes on every read and
    silently restates whenever the configuration is edited.
    """
    if state.exists:
        raise DomainError(f"Change {change_id} already exists")
    if not change_id:
        raise DomainError("change_id is required")
    if not subject_id:
        raise DomainError("subject_id is required")
    if workflow_for(subject_type) is None:
        raise DomainError(f"changes are not classified for record type: {subject_type}")
    if not (rationale or "").strip():
        raise DomainError("rationale is required")
    if not (after or {}) and not tuple(affected_artifacts or ()):
        raise DomainError("a change must move at least one field or artifact")
    return EVENT_PROPOSED, {
        "change_id": change_id, "subject_type": subject_type, "subject_id": subject_id,
        "rationale": rationale, "before": dict(before or {}), "after": dict(after or {}),
        "affected_artifacts": list(affected_artifacts or ()),
    }


def decide_classify(state: ChangeState) -> tuple[str, dict[str, Any]]:
    """Run the engine over the recorded proposal and record its verdict.

    Refuses a second classification. The tier is evidence of what was decided, and a
    record that could be reclassified in place would answer "what tier was this?"
    differently depending on when you asked. A superseding proposal is the way to
    revisit one.
    """
    _require_open(state)
    if state.classified:
        raise DomainError(f"Change is already classified as {state.change_class}")
    change_class = classify(subject_type=state.subject_type, before=state.before,
                            after=state.after,
                            affected_artifacts=state.affected_artifacts)
    workflow = workflow_for(state.subject_type)
    return EVENT_CLASSIFIED, {
        "change_class": change_class,
        "revalidation_depth": revalidation_depth_for(change_class, workflow),
        "workflow": workflow,
    }


def decide_supersede(state: ChangeState) -> tuple[str, dict[str, Any]]:
    """Close a proposal that a later one replaces, or that will not be pursued."""
    _require_open(state)
    return EVENT_SUPERSEDED, {}
