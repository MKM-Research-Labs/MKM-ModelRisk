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
"""Ingest-receipt read model.

Current-state projection of the last accepted ingestion per (artifact, repo) into
``ingest_receipts_view``. Backs ``GET /api/ingest/status/<artifact>``.
"""
from __future__ import annotations

from typing import Any

from src.database import read_all, read_view, replace_view
from src.ingest.receipt._state import apply, initial_state
from src.ingest.receipt.commands import AGGREGATE_TYPE, receipt_id

_VIEW = "ingest_receipts_view"
_COLUMNS = ("receipt_id", "data", "artifact", "content_hash", "version")


def _document(state) -> dict[str, Any]:
    return {
        "artifact": state.artifact,
        "source_repo": state.source_repo,
        "content_hash": state.content_hash,
        "provenance": state.provenance,
        "summary": state.summary,
    }


def rebuild_receipts_view(config=None) -> int:
    """Rebuild the read model from the event log; return the receipt count."""
    states: dict[str, tuple] = {}
    for event in read_all(config=config):
        if event.aggregate_type != AGGREGATE_TYPE:
            continue
        state, _ = states.get(event.aggregate_id, (initial_state(), 0))
        state = apply(state, event.event_type, event.payload)
        states[event.aggregate_id] = (state, event.stream_seq)
    rows = ((rid, _document(state), state.artifact, state.content_hash, version)
            for rid, (state, version) in states.items())
    return replace_view(_VIEW, _COLUMNS, rows, config=config)


def get_receipt(artifact: str, source_repo: str, config=None) -> dict[str, Any] | None:
    """Return the last accepted receipt for one (artifact, repo), or ``None``."""
    rows = read_view(
        _VIEW, _COLUMNS, where="receipt_id",
        value=receipt_id(artifact, source_repo), config=config,
    )
    return rows[0] if rows else None


def list_receipts(config=None) -> list[dict[str, Any]]:
    """Return every receipt, ordered by ``receipt_id``."""
    return read_view(_VIEW, _COLUMNS, order_by="receipt_id", config=config)
