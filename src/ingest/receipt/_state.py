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
"""Current-state fold for the ingest-receipt aggregate (pure, no I/O).

One aggregate per (artifact, source_repo); each ``PayloadIngested`` event records
an accepted ingestion — its content hash, provenance, and a summary. The state is
the most recent accepted receipt.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

EVENT_INGESTED = "PayloadIngested"


@dataclass(frozen=True)
class ReceiptState:
    """The most recent accepted ingestion for one (artifact, repo)."""

    exists: bool = False
    artifact: str | None = None
    source_repo: str | None = None
    content_hash: str | None = None
    provenance: dict[str, Any] | None = None
    summary: dict[str, Any] | None = None


def initial_state() -> ReceiptState:
    """The empty state before any payload has been accepted."""
    return ReceiptState()


def apply(state: ReceiptState, event_type: str, payload: dict[str, Any]) -> ReceiptState:
    """Fold one event into ``state``. Unknown event types are ignored."""
    if event_type == EVENT_INGESTED:
        return ReceiptState(
            exists=True,
            artifact=payload["artifact"],
            source_repo=payload["source_repo"],
            content_hash=payload["content_hash"],
            provenance=payload["provenance"],
            summary=payload.get("summary", {}),
        )
    return state
