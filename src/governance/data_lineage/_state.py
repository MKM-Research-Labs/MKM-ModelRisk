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
"""Current-state fold for the data-lineage manifest aggregate (pure, no I/O).

One aggregate per producing repo; each ``DataLineageIngested`` event carries the
latest full manifest that repo pushed. The state is simply the most recent
manifest plus its content hash and provenance.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

EVENT_INGESTED = "DataLineageIngested"


@dataclass(frozen=True)
class ManifestState:
    """The most recent data-lineage manifest ingested for one repo."""

    exists: bool = False
    manifest: dict[str, Any] | None = None
    content_hash: str | None = None
    provenance: dict[str, Any] | None = None


def initial_state() -> ManifestState:
    """The empty state of a repo that has ingested no manifest yet."""
    return ManifestState()


def apply(state: ManifestState, event_type: str, payload: dict[str, Any]) -> ManifestState:
    """Fold one event into ``state``. Unknown event types are ignored."""
    if event_type == EVENT_INGESTED:
        return ManifestState(
            exists=True,
            manifest=payload["manifest"],
            content_hash=payload["content_hash"],
            provenance=payload["provenance"],
        )
    return state
