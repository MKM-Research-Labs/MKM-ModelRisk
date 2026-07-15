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
