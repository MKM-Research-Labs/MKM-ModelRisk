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
"""Tamper-evidence: DB-grant immutability and hash-chain verification."""
from __future__ import annotations

import psycopg
import pytest

from src.database import (
    app_connection,
    append_event,
    owner_connection,
    read_stream,
    verify_chain,
)
from src.database._hash import compute_event_hash
from src.database.eventstore import _fmt_ts

_AT = "Model"
_AID = "TAMPER"


def _seed(count: int = 3) -> None:
    for i in range(count):
        append_event(
            aggregate_type=_AT,
            aggregate_id=_AID,
            event_type="Recorded",
            payload={"i": i},
            actor="system",
        )


def test_untampered_chain_verifies():
    _seed()
    assert verify_chain(aggregate_type=_AT, aggregate_id=_AID) is True


def test_payload_mutation_breaks_the_hash():
    _seed()
    with owner_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE events SET payload = '{\"i\": 999}'::jsonb "
                "WHERE aggregate_type = %s AND aggregate_id = %s AND stream_seq = 2",
                (_AT, _AID),
            )
    assert verify_chain(aggregate_type=_AT, aggregate_id=_AID) is False


def test_deleting_an_event_breaks_the_sequence():
    _seed()
    with owner_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM events "
                "WHERE aggregate_type = %s AND aggregate_id = %s AND stream_seq = 2",
                (_AT, _AID),
            )
    assert verify_chain(aggregate_type=_AT, aggregate_id=_AID) is False


def test_rehashed_event_breaks_prev_linkage():
    # Sophisticated tamper: alter event 1 AND recompute its own hash, so it is
    # self-consistent but event 2's prev_hash no longer points at it.
    _seed()
    first = read_stream(aggregate_type=_AT, aggregate_id=_AID)[0]
    forged = compute_event_hash(
        aggregate_type=first.aggregate_type,
        aggregate_id=first.aggregate_id,
        stream_seq=first.stream_seq,
        event_type=first.event_type,
        payload={"i": 999},
        actor=first.actor,
        reason=first.reason,
        recorded_at=_fmt_ts(first.recorded_at),
        prev_hash=first.prev_hash,
    )
    with owner_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE events SET payload = '{\"i\": 999}'::jsonb, event_hash = %s "
                "WHERE aggregate_type = %s AND aggregate_id = %s AND stream_seq = 1",
                (forged, _AT, _AID),
            )
    assert verify_chain(aggregate_type=_AT, aggregate_id=_AID) is False


def test_app_role_cannot_update_events():
    _seed(1)
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        with app_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE events SET actor = 'mallory'")


def test_app_role_cannot_delete_events():
    _seed(1)
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        with app_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM events")
