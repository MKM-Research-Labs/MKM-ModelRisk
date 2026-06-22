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
