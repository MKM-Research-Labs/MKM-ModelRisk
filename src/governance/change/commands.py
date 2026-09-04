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
"""Command handlers for the Change aggregate (event-sourced)."""
from __future__ import annotations

from typing import Any, Iterable

from src.database import Event, append_event, read_stream
from src.governance.change._rules import (decide_classify, decide_propose,
                                          decide_supersede)
from src.governance.change._state import ChangeState, apply, initial_state

AGGREGATE_TYPE = "Change"


def _load(change_id: str, config) -> tuple[ChangeState, int]:
    events = read_stream(aggregate_type=AGGREGATE_TYPE, aggregate_id=change_id,
                         config=config)
    state = initial_state()
    for event in events:
        state = apply(state, event.event_type, event.payload)
    return state, len(events)


def _record(change_id, decision, version, actor, reason, config) -> Event:
    event_type, payload = decision
    return append_event(
        aggregate_type=AGGREGATE_TYPE, aggregate_id=change_id,
        event_type=event_type, payload=payload, actor=actor, reason=reason,
        expected_version=version, config=config)


def propose_change(*, change_id: str, subject_type: str, subject_id: str,
                   rationale: str, before: dict[str, Any] | None = None,
                   after: dict[str, Any] | None = None,
                   affected_artifacts: Iterable[str] = (), actor: str,
                   reason: str = "", config=None) -> Event:
    """Propose a change against a model, ML Application or AI System."""
    state, version = _load(change_id, config)
    decision = decide_propose(
        state, change_id=change_id, subject_type=subject_type, subject_id=subject_id,
        rationale=rationale, before=before or {}, after=after or {},
        affected_artifacts=affected_artifacts)
    return _record(change_id, decision, version, actor, reason, config)


def classify_change(*, change_id: str, actor: str, reason: str = "",
                    config=None) -> Event:
    """Classify a proposed change and record the revalidation depth it implies."""
    state, version = _load(change_id, config)
    return _record(change_id, decide_classify(state), version, actor, reason, config)


def supersede_change(*, change_id: str, actor: str, reason: str = "",
                     config=None) -> Event:
    """Close a proposal that a later one replaces, or that will not be pursued."""
    state, version = _load(change_id, config)
    return _record(change_id, decide_supersede(state), version, actor, reason, config)
