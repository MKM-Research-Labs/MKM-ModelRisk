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
"""Model-chain read model.

A current-state projection of the latest chain per producing repo into
``model_chain_view``. Derived and fully rebuildable: ``rebuild_model_chain_view``
replays the log from zero.
"""
from __future__ import annotations

from typing import Any

from src.database import read_all, read_view, replace_view
from src.governance.model_chain._state import apply, initial_state
from src.governance.model_chain.commands import AGGREGATE_TYPE

_VIEW = "model_chain_view"
_COLUMNS = ("source_repo", "data", "content_hash", "version")


def _document(state) -> dict[str, Any]:
    """The stored chain plus provenance and derived count, as one JSONB doc.

    Only ever called for aggregates that have an ingested chain, so
    ``state.chain`` is always a dict here.
    """
    chain = state.chain
    return {
        "chain": chain,
        "provenance": state.provenance,
        "link_count": len(chain.get("links", [])),
    }


def rebuild_model_chain_view(config=None) -> int:
    """Rebuild the read model from the event log; return the repo count."""
    states: dict[str, tuple] = {}
    for event in read_all(config=config):
        if event.aggregate_type != AGGREGATE_TYPE:
            continue
        state, _ = states.get(event.aggregate_id, (initial_state(), 0))
        state = apply(state, event.event_type, event.payload)
        states[event.aggregate_id] = (state, event.stream_seq)
    rows = ((repo, _document(state), state.content_hash, version)
            for repo, (state, version) in states.items())
    return replace_view(_VIEW, _COLUMNS, rows, config=config)


def get_chain(source_repo: str, config=None) -> dict[str, Any] | None:
    """Return the latest chain document for one repo, or ``None``."""
    rows = read_view(_VIEW, _COLUMNS, where="source_repo", value=source_repo, config=config)
    return rows[0] if rows else None


def list_chains(config=None) -> list[dict[str, Any]]:
    """Return the latest chain for every repo, ordered by ``source_repo``."""
    return read_view(_VIEW, _COLUMNS, order_by="source_repo", config=config)
