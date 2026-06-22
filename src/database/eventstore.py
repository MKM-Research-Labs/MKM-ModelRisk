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
"""Append-only event store with a per-stream tamper-evident hash chain.

Events are grouped into streams keyed by ``(aggregate_type, aggregate_id)``.
Within a stream ``stream_seq`` is a 1-based, gap-free counter; a UNIQUE
constraint makes concurrent appends to the same position impossible. Immutability
is enforced at the database-grant level (the app role cannot UPDATE/DELETE), and
the hash chain makes any privileged tampering detectable.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from psycopg.types.json import Jsonb

from src.database._connection import app_connection
from src.database._hash import compute_event_hash

_SELECT_COLUMNS = (
    "global_seq, event_id, aggregate_type, aggregate_id, stream_seq, "
    "event_type, payload, actor, reason, recorded_at, prev_hash, event_hash"
)


class ConcurrencyError(RuntimeError):
    """Raised when ``expected_version`` does not match the stream head."""


@dataclass(frozen=True)
class Event:
    """One recorded event, as returned by the store."""

    global_seq: int
    event_id: str
    aggregate_type: str
    aggregate_id: str
    stream_seq: int
    event_type: str
    payload: dict[str, Any]
    actor: str
    reason: str | None
    recorded_at: datetime
    prev_hash: str | None
    event_hash: str


def _fmt_ts(value: datetime) -> str:
    """Canonical UTC ISO-8601 string used for hashing."""
    return value.astimezone(timezone.utc).isoformat()


def _row_to_event(row: tuple) -> Event:
    return Event(
        global_seq=row[0],
        event_id=str(row[1]),
        aggregate_type=row[2],
        aggregate_id=row[3],
        stream_seq=row[4],
        event_type=row[5],
        payload=row[6],
        actor=row[7],
        reason=row[8],
        recorded_at=row[9],
        prev_hash=row[10],
        event_hash=row[11],
    )


def append_event(
    *,
    aggregate_type: str,
    aggregate_id: str,
    event_type: str,
    payload: dict[str, Any],
    actor: str,
    reason: str | None = None,
    expected_version: int | None = None,
    config=None,
) -> Event:
    """Append one event to a stream and return the stored record.

    ``expected_version`` is the caller's view of the current stream length;
    when supplied and it disagrees with the stored head a ``ConcurrencyError``
    is raised (optimistic concurrency control).
    """
    recorded_at = datetime.now(timezone.utc)
    with app_connection(config) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT stream_seq, event_hash FROM events "
                "WHERE aggregate_type = %s AND aggregate_id = %s "
                "ORDER BY stream_seq DESC LIMIT 1",
                (aggregate_type, aggregate_id),
            )
            head = cur.fetchone()
            current_version = head[0] if head else 0
            prev_hash = head[1] if head else None
            if expected_version is not None and expected_version != current_version:
                raise ConcurrencyError(
                    f"expected version {expected_version}, found "
                    f"{current_version} for {aggregate_type}/{aggregate_id}"
                )
            stream_seq = current_version + 1
            event_hash = compute_event_hash(
                aggregate_type=aggregate_type,
                aggregate_id=aggregate_id,
                stream_seq=stream_seq,
                event_type=event_type,
                payload=payload,
                actor=actor,
                reason=reason,
                recorded_at=_fmt_ts(recorded_at),
                prev_hash=prev_hash,
            )
            cur.execute(
                "INSERT INTO events (aggregate_type, aggregate_id, stream_seq, "
                "event_type, payload, actor, reason, recorded_at, prev_hash, "
                "event_hash) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "
                f"RETURNING {_SELECT_COLUMNS}",
                (
                    aggregate_type,
                    aggregate_id,
                    stream_seq,
                    event_type,
                    Jsonb(payload),
                    actor,
                    reason,
                    recorded_at,
                    prev_hash,
                    event_hash,
                ),
            )
            return _row_to_event(cur.fetchone())


def read_stream(*, aggregate_type: str, aggregate_id: str, config=None) -> list[Event]:
    """Return every event in one stream, ordered by ``stream_seq``."""
    with app_connection(config) as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT {_SELECT_COLUMNS} FROM events "
                "WHERE aggregate_type = %s AND aggregate_id = %s "
                "ORDER BY stream_seq ASC",
                (aggregate_type, aggregate_id),
            )
            return [_row_to_event(r) for r in cur.fetchall()]


def read_all(
    *, after_global_seq: int = 0, limit: int | None = None, config=None
) -> list[Event]:
    """Return events across all streams in global order (for projections)."""
    sql = (
        f"SELECT {_SELECT_COLUMNS} FROM events "
        "WHERE global_seq > %s ORDER BY global_seq ASC"
    )
    params: list[Any] = [after_global_seq]
    if limit is not None:
        sql += " LIMIT %s"
        params.append(limit)
    with app_connection(config) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return [_row_to_event(r) for r in cur.fetchall()]


def verify_chain(*, aggregate_type: str, aggregate_id: str, config=None) -> bool:
    """Recompute a stream's hash chain; ``False`` if any event was tampered."""
    events = read_stream(
        aggregate_type=aggregate_type, aggregate_id=aggregate_id, config=config
    )
    expected_prev: str | None = None
    expected_seq = 1
    for event in events:
        if event.stream_seq != expected_seq:
            return False
        if event.prev_hash != expected_prev:
            return False
        recomputed = compute_event_hash(
            aggregate_type=event.aggregate_type,
            aggregate_id=event.aggregate_id,
            stream_seq=event.stream_seq,
            event_type=event.event_type,
            payload=event.payload,
            actor=event.actor,
            reason=event.reason,
            recorded_at=_fmt_ts(event.recorded_at),
            prev_hash=event.prev_hash,
        )
        if recomputed != event.event_hash:
            return False
        expected_prev = event.event_hash
        expected_seq += 1
    return True
