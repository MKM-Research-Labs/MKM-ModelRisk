# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
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
