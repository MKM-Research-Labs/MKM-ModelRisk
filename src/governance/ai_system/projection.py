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
"""AI System read model: a projection of the event log into ``ai_system_view``."""
from __future__ import annotations

from typing import Any

from src.database import read_all, read_view, replace_view
from src.governance.ai_system._state import apply, initial_state, record_data
from src.governance.ai_system.commands import AGGREGATE_TYPE
from src.governance.ai_system.complexity import grid_position

_VIEW = "ai_system_view"
_COLUMNS = ("ai_system_id", "data", "retired", "version")


def rebuild_ai_system_view(config=None) -> int:
    """Rebuild the read model from the event log; return the AI System count."""
    states: dict[str, tuple] = {}
    for event in read_all(config=config):
        if event.aggregate_type != AGGREGATE_TYPE:
            continue
        state, _ = states.get(event.aggregate_id, (initial_state(), 0))
        state = apply(state, event.event_type, event.payload)
        states[event.aggregate_id] = (state, event.stream_seq)
    rows = ((ai_system_id, record_data(state), state.retired, version)
            for ai_system_id, (state, version) in states.items())
    return replace_view(_VIEW, _COLUMNS, rows, config=config)


def _placed(row: dict[str, Any]) -> dict[str, Any]:
    """The row with its grid position, resolved now rather than stored in the view:
    an edit to the grid tables re-places every system without a rebuild."""
    return {**row, "grid": grid_position(row.get("data") or {})}


def get_ai_system(ai_system_id: str, config=None) -> dict[str, Any] | None:
    rows = read_view(_VIEW, _COLUMNS, where="ai_system_id", value=ai_system_id,
                     config=config)
    return _placed(rows[0]) if rows else None


def list_ai_systems(config=None, *, include_retired: bool = False) -> list[dict[str, Any]]:
    """The live AI Systems, ordered by ``ai_system_id``.

    Hibernated records are left out by default, on the same reasoning as
    ``list_models``: a retired record carries no governance obligations, so counting
    it drags every estate-wide figure against something nobody will ever complete.
    The record survives in the log. ``include_retired=True`` is for reads that are
    *about* a particular record rather than about the estate.
    """
    rows = [_placed(row) for row in read_view(_VIEW, _COLUMNS, order_by="ai_system_id",
                                              config=config)]
    return rows if include_retired else [row for row in rows if not row.get("retired")]
