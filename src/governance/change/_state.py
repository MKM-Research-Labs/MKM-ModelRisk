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
"""Current-state fold for the Change aggregate (pure, no I/O).

A Change is a proposal about another record, not a property of it. Keeping it as its
own aggregate is what lets several proposals stand against one model at once, and what
keeps the tier a *recorded fact* -- classified on a given day against the triggers that
stood then -- rather than something recomputed from config every time a screen loads.

The three event names are permanent. The log is append-only, so a rename leaves every
existing event unreadable by this fold; and an event type this ``apply`` does not handle
is dropped silently from the read model while remaining in the log, which reads as data
loss and is not.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any

EVENT_PROPOSED = "ChangeProposed"
EVENT_CLASSIFIED = "ChangeClassified"
EVENT_SUPERSEDED = "ChangeSuperseded"


@dataclass(frozen=True)
class ChangeState:
    """The reconstructed current state of one proposed change."""

    exists: bool = False
    superseded: bool = False
    subject_type: str = ""
    subject_id: str = ""
    rationale: str = ""
    # The proposed movement, as it was described when proposed. Held so the tier can
    # be re-derived and checked, and so a reader can see what was actually asked for.
    before: dict[str, Any] = field(default_factory=dict)
    after: dict[str, Any] = field(default_factory=dict)
    affected_artifacts: tuple[str, ...] = ()
    change_class: str = ""
    revalidation_depth: str = ""

    @property
    def classified(self) -> bool:
        return bool(self.change_class)


def initial_state() -> ChangeState:
    return ChangeState()


def record_data(state: ChangeState) -> dict[str, Any]:
    """A state as the flat record shape everything downstream reads."""
    return {
        "subject_type": state.subject_type,
        "subject_id": state.subject_id,
        "rationale": state.rationale,
        "before": dict(state.before),
        "after": dict(state.after),
        "affected_artifacts": list(state.affected_artifacts),
        "change_class": state.change_class,
        "revalidation_depth": state.revalidation_depth,
        "superseded": state.superseded,
    }


def apply(state: ChangeState, event_type: str,
          payload: dict[str, Any]) -> ChangeState:
    """Fold one event into ``state``. Unknown event types are ignored."""
    if event_type == EVENT_PROPOSED:
        return ChangeState(
            exists=True,
            subject_type=payload.get("subject_type", ""),
            subject_id=payload.get("subject_id", ""),
            rationale=payload.get("rationale", ""),
            before=dict(payload.get("before") or {}),
            after=dict(payload.get("after") or {}),
            affected_artifacts=tuple(payload.get("affected_artifacts") or ()),
        )
    if event_type == EVENT_CLASSIFIED:
        return replace(state, change_class=payload.get("change_class", ""),
                       revalidation_depth=payload.get("revalidation_depth", ""))
    if event_type == EVENT_SUPERSEDED:
        # The proposal stays readable. Superseded is a fact about whether anyone should
        # still act on it, not an erasure -- the log could not erase it in any case.
        return replace(state, superseded=True)
    return state


__all__ = ["ChangeState", "initial_state", "record_data", "apply",
           "EVENT_PROPOSED", "EVENT_CLASSIFIED", "EVENT_SUPERSEDED"]
