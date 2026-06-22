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
"""Tamper-evident hashing for the event log.

Each event carries ``event_hash`` = SHA-256 over its own fields plus the
previous event's hash in the same stream. Recomputing the chain detects any
after-the-fact mutation of a stored event (see ``eventstore.verify_chain``).
"""
from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_payload(payload: dict[str, Any]) -> str:
    """Deterministic JSON encoding of a payload (stable key order)."""
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )


def compute_event_hash(
    *,
    aggregate_type: str,
    aggregate_id: str,
    stream_seq: int,
    event_type: str,
    payload: dict[str, Any],
    actor: str,
    reason: str | None,
    recorded_at: str,
    prev_hash: str | None,
) -> str:
    """Compute the chained SHA-256 hash for one event."""
    material = "|".join(
        [
            aggregate_type,
            aggregate_id,
            str(stream_seq),
            event_type,
            canonical_payload(payload),
            actor,
            reason or "",
            recorded_at,
            prev_hash or "",
        ]
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()
