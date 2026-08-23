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
"""ML Application read model: a projection of the event log into ``ml_application_view``."""
from __future__ import annotations

from typing import Any

from src.database import read_all, read_view, replace_view
from config.governance import TRAINING_RUNS_COLLECTION
from src.governance.ml_application._state import apply, initial_state
from src.governance.ml_application.training import completeness
from src.governance.ml_application.commands import AGGREGATE_TYPE

_VIEW = "ml_application_view"
_COLUMNS = ("ml_application_id", "data", "retired", "version")


def _document(state) -> dict[str, Any]:
    data = dict(state.fields)
    for collection, items in state.collections.items():
        data[collection] = list(items)
    # Derived, like a Product's identifier: computed here so the tab counter, the
    # state on the page and anything that audits the estate all read one figure
    # rather than three that can disagree. The most recent train is the one in
    # force; earlier ones are history and are not re-scored.
    runs = data.get(TRAINING_RUNS_COLLECTION) or []
    data["training_completeness"] = completeness(runs[-1] if runs else None)
    return data


def rebuild_ml_application_view(config=None) -> int:
    """Rebuild the read model from the event log; return the ML Application count."""
    states: dict[str, tuple] = {}
    for event in read_all(config=config):
        if event.aggregate_type != AGGREGATE_TYPE:
            continue
        state, _ = states.get(event.aggregate_id, (initial_state(), 0))
        state = apply(state, event.event_type, event.payload)
        states[event.aggregate_id] = (state, event.stream_seq)
    rows = ((ml_application_id, _document(state), state.retired, version)
            for ml_application_id, (state, version) in states.items())
    return replace_view(_VIEW, _COLUMNS, rows, config=config)


def get_ml_application(ml_application_id: str, config=None) -> dict[str, Any] | None:
    rows = read_view(_VIEW, _COLUMNS, where="ml_application_id",
                     value=ml_application_id, config=config)
    return rows[0] if rows else None


def list_ml_applications(config=None, *,
                         include_retired: bool = False) -> list[dict[str, Any]]:
    """The live ML Applications, ordered by ``ml_application_id``.

    Hibernated records are left out by default, on the same reasoning as
    ``list_models``: a retired record carries no governance obligations, so
    counting it drags every estate-wide figure against something nobody will
    ever complete. Excluding it is the honest default; the record survives in
    the log.

    ``include_retired=True`` is for reads that are *about* a particular record
    rather than about the estate.
    """
    rows = read_view(_VIEW, _COLUMNS, order_by="ml_application_id", config=config)
    return rows if include_retired else [row for row in rows if not row.get("retired")]
