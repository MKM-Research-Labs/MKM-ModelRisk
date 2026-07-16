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
"""Tests for the append-only event store."""
from __future__ import annotations

import pytest

from config import DatabaseConfig
from src.database import (
    ConcurrencyError,
    append_event,
    read_all,
    read_stream,
    verify_chain,
)


def _append(**overrides):
    base = dict(
        aggregate_type="Model",
        aggregate_id="EXAMPLE-001",
        event_type="RegisterModel",
        payload={"name": "Example"},
        actor="alice",
    )
    base.update(overrides)
    return append_event(**base)


def test_first_append_starts_at_one_with_no_prev_hash():
    event = _append()
    assert event.stream_seq == 1
    assert event.prev_hash is None
    assert event.event_hash
    assert event.actor == "alice"
    assert event.payload == {"name": "Example"}
    assert event.global_seq >= 1


def test_subsequent_append_chains_to_previous_hash():
    first = _append()
    second = _append(event_type="UpdateField", payload={"field": "owner"})
    assert second.stream_seq == 2
    assert second.prev_hash == first.event_hash


def test_read_stream_returns_events_in_order():
    _append()
    _append(event_type="UpdateField", payload={})
    events = read_stream(aggregate_type="Model", aggregate_id="EXAMPLE-001")
    assert [e.stream_seq for e in events] == [1, 2]


def test_streams_are_isolated_by_aggregate_id():
    _append(aggregate_id="M1")
    _append(aggregate_id="M2")
    assert len(read_stream(aggregate_type="Model", aggregate_id="M1")) == 1
    assert len(read_stream(aggregate_type="Model", aggregate_id="M2")) == 1


def test_read_all_is_global_order_with_filters():
    first = _append(aggregate_id="M1")
    second = _append(aggregate_id="M2")
    everything = read_all()
    assert [e.global_seq for e in everything] == [first.global_seq, second.global_seq]
    after = read_all(after_global_seq=first.global_seq)
    assert [e.global_seq for e in after] == [second.global_seq]
    assert len(read_all(limit=1)) == 1


def test_reason_is_recorded():
    event = _append(reason="initial load")
    assert event.reason == "initial load"


def test_expected_version_match_allows_append():
    _append()
    event = _append(expected_version=1)
    assert event.stream_seq == 2


def test_expected_version_zero_on_empty_stream():
    event = _append(expected_version=0)
    assert event.stream_seq == 1


def test_expected_version_mismatch_raises_concurrency_error():
    _append()
    with pytest.raises(ConcurrencyError):
        _append(expected_version=0)


def test_explicit_config_is_accepted():
    config = DatabaseConfig.from_env()
    event = append_event(
        aggregate_type="Model",
        aggregate_id="CFG",
        event_type="RegisterModel",
        payload={},
        actor="system",
        config=config,
    )
    stream = read_stream(aggregate_type="Model", aggregate_id="CFG", config=config)
    assert event.stream_seq == 1
    assert stream[0].event_hash == event.event_hash


def test_chain_is_valid_after_appends():
    _append()
    _append(event_type="UpdateField", payload={"x": 1})
    assert verify_chain(aggregate_type="Model", aggregate_id="EXAMPLE-001") is True


def test_verify_chain_of_empty_stream_is_valid():
    assert verify_chain(aggregate_type="Model", aggregate_id="DOES-NOT-EXIST") is True
