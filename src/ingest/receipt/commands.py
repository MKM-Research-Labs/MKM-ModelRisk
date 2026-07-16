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
"""Command handler for the ingest-receipt aggregate.

One stream per ``(artifact, source_repo)``. Each accepted ingestion appends a
``PayloadIngested`` event, so the stream is the provenance history of what that
producer has fed the collector.
"""
from __future__ import annotations

from typing import Any

from src.database import Event, append_event, read_stream
from src.ingest.receipt._rules import decide_record
from src.ingest.receipt._state import ReceiptState, apply, initial_state

AGGREGATE_TYPE = "IngestReceipt"


def receipt_id(artifact: str, source_repo: str) -> str:
    """The aggregate id for one producer's stream of a given artifact."""
    return f"{artifact}:{source_repo}"


def _load(rid: str, config) -> tuple[ReceiptState, int]:
    events = read_stream(aggregate_type=AGGREGATE_TYPE, aggregate_id=rid, config=config)
    state = initial_state()
    for event in events:
        state = apply(state, event.event_type, event.payload)
    return state, len(events)


def record_receipt(
    *, artifact: str, source_repo: str, content_hash: str,
    provenance: dict[str, Any], summary: dict[str, Any], actor: str,
    reason: str | None = None, config=None,
) -> Event:
    """Record an accepted ingestion for ``(artifact, source_repo)``."""
    rid = receipt_id(artifact, source_repo)
    state, version = _load(rid, config)
    event_type, payload = decide_record(
        state, artifact=artifact, source_repo=source_repo,
        content_hash=content_hash, provenance=provenance, summary=summary,
    )
    return append_event(
        aggregate_type=AGGREGATE_TYPE, aggregate_id=rid, event_type=event_type,
        payload=payload, actor=actor, reason=reason, expected_version=version,
        config=config,
    )
