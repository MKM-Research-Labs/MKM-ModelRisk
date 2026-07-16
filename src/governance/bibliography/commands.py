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
"""Commands to maintain bibliography references."""
from __future__ import annotations

from typing import Any

from config.governance import BIBLIOGRAPHY_SPECS
from src.database import Event, append_event
from src.governance import collections as coll
from src.governance.bibliography._store import (
    AGGREGATE_ID,
    AGGREGATE_TYPE,
    COLLECTION,
    load,
)


def _record(decision, version, actor, reason, config) -> Event:
    event_type, payload = decision
    return append_event(
        aggregate_type=AGGREGATE_TYPE, aggregate_id=AGGREGATE_ID, event_type=event_type,
        payload=payload, actor=actor, reason=reason, expected_version=version, config=config,
    )


def add_reference(*, fields: dict[str, Any], actor: str, reason: str | None = None, config=None) -> Event:
    """Add a bibliography reference."""
    state, version = load(config)
    decision = coll.decide_add(state, BIBLIOGRAPHY_SPECS, collection=COLLECTION, fields=fields)
    return _record(decision, version, actor, reason, config)


def update_reference(
    *, item_id: str, fields: dict[str, Any], actor: str, reason: str | None = None, config=None,
) -> Event:
    """Update fields of a reference."""
    state, version = load(config)
    decision = coll.decide_update(
        state, BIBLIOGRAPHY_SPECS, collection=COLLECTION, item_id=item_id, fields=fields
    )
    return _record(decision, version, actor, reason, config)


def remove_reference(*, item_id: str, actor: str, reason: str | None = None, config=None) -> Event:
    """Remove a reference."""
    state, version = load(config)
    decision = coll.decide_remove(state, BIBLIOGRAPHY_SPECS, collection=COLLECTION, item_id=item_id)
    return _record(decision, version, actor, reason, config)
