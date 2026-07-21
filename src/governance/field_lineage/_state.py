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
"""Current-state fold for the field-lineage registry aggregate (pure, no I/O).

One aggregate per producing repo; each ``FieldLineageIngested`` event carries the
latest full catalogue that repo pushed, mapping every field on every report to the
source its value comes from (BCBS 239 Principle 3). The state is simply the most
recent registry plus its content hash and provenance.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

EVENT_INGESTED = "FieldLineageIngested"


@dataclass(frozen=True)
class RegistryState:
    """The most recent field-lineage registry ingested for one repo."""

    exists: bool = False
    registry: dict[str, Any] | None = None
    content_hash: str | None = None
    provenance: dict[str, Any] | None = None


def initial_state() -> RegistryState:
    """The empty state of a repo that has ingested no registry yet."""
    return RegistryState()


def apply(state: RegistryState, event_type: str, payload: dict[str, Any]) -> RegistryState:
    """Fold one event into ``state``. Unknown event types are ignored."""
    if event_type == EVENT_INGESTED:
        return RegistryState(
            exists=True,
            registry=payload["registry"],
            content_hash=payload["content_hash"],
            provenance=payload["provenance"],
        )
    return state
