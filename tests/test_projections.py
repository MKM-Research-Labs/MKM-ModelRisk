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
"""Tests for projection replay (rebuilding a read model from the event log)."""
from __future__ import annotations

from src.database import append_event, replay


def _append(aggregate_id, event_type, payload):
    return append_event(
        aggregate_type="Model",
        aggregate_id=aggregate_id,
        event_type=event_type,
        payload=payload,
        actor="system",
    )


def test_replay_rebuilds_read_model_from_zero():
    _append("M1", "RegisterModel", {"name": "Alpha"})
    _append("M2", "RegisterModel", {"name": "Beta"})
    _append("M1", "UpdateField", {"name": "Alpha v2"})

    names: dict[str, str] = {}

    def handler(event):
        names[event.aggregate_id] = event.payload["name"]

    replayed = replay(handler)
    assert replayed == 3
    assert names == {"M1": "Alpha v2", "M2": "Beta"}


def test_replay_after_checkpoint_returns_only_new_events():
    first = _append("M1", "RegisterModel", {"name": "Alpha"})
    _append("M2", "RegisterModel", {"name": "Beta"})

    seen: list[str] = []
    replayed = replay(
        lambda event: seen.append(event.aggregate_id),
        after_global_seq=first.global_seq,
    )
    assert replayed == 1
    assert seen == ["M2"]


def test_replay_with_no_events_returns_zero():
    assert replay(lambda event: None) == 0
