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
"""Change read model: a projection of the event log into ``change_view``.

Kept on the standard view shape with two extra columns -- ``subject_type`` and
``subject_id`` -- because every read this serves is "what is outstanding against THIS
record", and a detail screen should not have to pull the whole register to answer it.
"""
from __future__ import annotations

from typing import Any

from src.database import read_all, read_view, replace_view
from src.governance.change._state import apply, initial_state, record_data
from src.governance.change.commands import AGGREGATE_TYPE

_VIEW = "change_view"
_COLUMNS = ("change_id", "data", "subject_type", "subject_id", "superseded", "version")


def rebuild_change_view(config=None) -> int:
    """Rebuild the read model from the event log; return the change count."""
    states: dict[str, tuple] = {}
    for event in read_all(config=config):
        if event.aggregate_type != AGGREGATE_TYPE:
            continue
        state, _ = states.get(event.aggregate_id, (initial_state(), 0))
        state = apply(state, event.event_type, event.payload)
        states[event.aggregate_id] = (state, event.stream_seq)
    rows = ((change_id, record_data(state), state.subject_type, state.subject_id,
             state.superseded, version)
            for change_id, (state, version) in states.items())
    return replace_view(_VIEW, _COLUMNS, rows, config=config)


def get_change(change_id: str, config=None) -> dict[str, Any] | None:
    rows = read_view(_VIEW, _COLUMNS, where="change_id", value=change_id, config=config)
    return rows[0] if rows else None


def list_changes(config=None, *, include_superseded: bool = True) -> list[dict[str, Any]]:
    """Every change in the register, ordered by ``change_id``.

    Superseded proposals are included by default, the opposite of ``list_models``'
    treatment of retired records: the register is read as a history of what was
    proposed, and a proposal that was dropped is part of that history rather than
    noise dragging an estate-wide figure.
    """
    rows = read_view(_VIEW, _COLUMNS, order_by="change_id", config=config)
    return rows if include_superseded else [r for r in rows if not r.get("superseded")]


def list_changes_for(subject_type: str, subject_id: str, config=None, *,
                     include_superseded: bool = True) -> list[dict[str, Any]]:
    """The changes proposed against one record, newest id last."""
    rows = read_view(_VIEW, _COLUMNS, where="subject_id", value=subject_id,
                     config=config)
    rows = [r for r in rows if r.get("subject_type") == subject_type]
    if not include_superseded:
        rows = [r for r in rows if not r.get("superseded")]
    return sorted(rows, key=lambda r: r["change_id"])
