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
"""Model-inventory read model.

A current-state projection of the event log into ``model_inventory_view``. The
projection is derived and fully rebuildable: ``rebuild_inventory_view`` replays
the log from zero. Queries (``get_model``, ``list_models``) serve the read side.
"""
from __future__ import annotations

from typing import Any

from src.database import read_all, read_view, replace_view
from src.governance.model_inventory._state import apply, initial_state
from src.governance.model_inventory.commands import AGGREGATE_TYPE

_VIEW = "model_inventory_view"
_COLUMNS = ("model_id", "data", "retired", "version")


def _document(state) -> dict[str, Any]:
    """Scalar fields plus each non-empty collection, as one JSONB document."""
    data = dict(state.fields)
    for collection, items in state.collections.items():
        data[collection] = list(items)
    return data


def rebuild_inventory_view(config=None) -> int:
    """Rebuild the read model from the event log; return the model count."""
    states: dict[str, tuple] = {}
    for event in read_all(config=config):
        if event.aggregate_type != AGGREGATE_TYPE:
            continue
        state, _ = states.get(event.aggregate_id, (initial_state(), 0))
        state = apply(state, event.event_type, event.payload)
        states[event.aggregate_id] = (state, event.stream_seq)
    rows = ((model_id, _document(state), state.retired, version)
            for model_id, (state, version) in states.items())
    return replace_view(_VIEW, _COLUMNS, rows, config=config)


def get_model(model_id: str, config=None) -> dict[str, Any] | None:
    """Return one model's current state, or ``None`` if not present."""
    rows = read_view(_VIEW, _COLUMNS, where="model_id", value=model_id, config=config)
    return rows[0] if rows else None


def list_models(config=None) -> list[dict[str, Any]]:
    """Return all models in the inventory, ordered by ``model_id``."""
    return read_view(_VIEW, _COLUMNS, order_by="model_id", config=config)
