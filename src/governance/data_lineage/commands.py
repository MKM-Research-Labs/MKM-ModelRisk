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
"""Command handler for the data-lineage manifest aggregate.

One stream per producing repo (``aggregate_id = source_repo``). Each push appends
a ``DataLineageIngested`` event carrying the full manifest. Pushing an identical
manifest (same content hash as the current head) is idempotent: no event is
appended and ``None`` is returned.
"""
from __future__ import annotations

from typing import Any

from src.database import Event, append_event, read_stream
from src.governance.data_lineage._rules import decide_ingest
from src.governance.data_lineage._state import ManifestState, apply, initial_state

AGGREGATE_TYPE = "DataLineageManifest"


def _load(source_repo: str, config) -> tuple[ManifestState, int]:
    events = read_stream(
        aggregate_type=AGGREGATE_TYPE, aggregate_id=source_repo, config=config
    )
    state = initial_state()
    for event in events:
        state = apply(state, event.event_type, event.payload)
    return state, len(events)


def ingest_data_lineage(
    *, source_repo: str, manifest: dict[str, Any], provenance: dict[str, Any],
    content_hash: str, actor: str, reason: str | None = None, config=None,
) -> Event | None:
    """Store a pushed manifest for ``source_repo``.

    Returns the appended event, or ``None`` if the manifest is byte-identical to
    the one already stored (idempotent no-op).
    """
    state, version = _load(source_repo, config)
    if state.exists and state.content_hash == content_hash:
        return None
    event_type, payload = decide_ingest(
        state, manifest=manifest, provenance=provenance, content_hash=content_hash
    )
    return append_event(
        aggregate_type=AGGREGATE_TYPE, aggregate_id=source_repo,
        event_type=event_type, payload=payload, actor=actor, reason=reason,
        expected_version=version, config=config,
    )
