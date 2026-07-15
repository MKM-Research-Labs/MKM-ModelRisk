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
