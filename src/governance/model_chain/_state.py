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
"""Current-state fold for the model-chain aggregate (pure, no I/O).

One aggregate per producing repo; each ``ModelChainIngested`` event carries the
latest full chain (the 'string of pearls' dependency graph) that repo pushed. The
state is simply the most recent chain plus its content hash and provenance.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

EVENT_INGESTED = "ModelChainIngested"


@dataclass(frozen=True)
class ChainState:
    """The most recent model chain ingested for one repo."""

    exists: bool = False
    chain: dict[str, Any] | None = None
    content_hash: str | None = None
    provenance: dict[str, Any] | None = None


def initial_state() -> ChainState:
    """The empty state of a repo that has ingested no chain yet."""
    return ChainState()


def apply(state: ChainState, event_type: str, payload: dict[str, Any]) -> ChainState:
    """Fold one event into ``state``. Unknown event types are ignored."""
    if event_type == EVENT_INGESTED:
        return ChainState(
            exists=True,
            chain=payload["chain"],
            content_hash=payload["content_hash"],
            provenance=payload["provenance"],
        )
    return state
