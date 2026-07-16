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
"""Bibliography store: a global, event-sourced reference list."""
from __future__ import annotations

from src.database import read_stream
from src.governance import collections as coll

AGGREGATE_TYPE = "Bibliography"
AGGREGATE_ID = "global"
COLLECTION = "references"


def load(config=None) -> tuple[dict, int]:
    state: dict = {}
    version = 0
    for event in read_stream(
        aggregate_type=AGGREGATE_TYPE, aggregate_id=AGGREGATE_ID, config=config
    ):
        folded = coll.fold(state, event.event_type, event.payload)
        if folded is not None:
            state = folded
        version = event.stream_seq
    return state, version


def get_references(config=None) -> list:
    """All bibliography references."""
    state, _ = load(config)
    return list(state.get(COLLECTION, ()))
