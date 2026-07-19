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
"""Model-handoff read model.

A current-state projection of the handoff event log into ``model_handoff_view``,
one row per declared edge. Derived and fully rebuildable — ``rebuild_handoff_view``
replays the log from zero.
"""
from __future__ import annotations

from typing import Any

from src.database import read_all, read_view, replace_view
from src.governance.model_handoff._state import apply, initial_state
from src.governance.model_handoff.commands import AGGREGATE_TYPE, handoff_id

_VIEW = "model_handoff_view"
_COLUMNS = ("handoff_id", "data", "version")


def _document(state) -> dict[str, Any]:
    """Scalar fields plus each non-empty collection, as one JSONB document."""
    data = dict(state.fields)
    for collection, items in state.collections.items():
        data[collection] = list(items)
    return data


def rebuild_handoff_view(config=None) -> int:
    """Rebuild the read model from the event log; return the handoff count."""
    states: dict[str, tuple] = {}
    for event in read_all(config=config):
        if event.aggregate_type != AGGREGATE_TYPE:
            continue
        state, _ = states.get(event.aggregate_id, (initial_state(), 0))
        state = apply(state, event.event_type, event.payload)
        states[event.aggregate_id] = (state, event.stream_seq)
    rows = ((hid, _document(state), version) for hid, (state, version) in states.items())
    return replace_view(_VIEW, _COLUMNS, rows, config=config)


def get_handoff(hid: str, config=None) -> dict[str, Any] | None:
    """Return one handoff by its id, or ``None`` if not declared."""
    rows = read_view(_VIEW, _COLUMNS, where="handoff_id", value=hid, config=config)
    return rows[0] if rows else None


def get_handoff_for_edge(from_model: str, to_model: str, config=None) -> dict[str, Any] | None:
    """Return the handoff on a given edge, or ``None`` if none is declared."""
    return get_handoff(handoff_id(from_model, to_model), config=config)


def list_handoffs(config=None) -> list[dict[str, Any]]:
    """Return every declared handoff, ordered by id."""
    return read_view(_VIEW, _COLUMNS, order_by="handoff_id", config=config)
