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
"""Seeding collection items onto an aggregate immediately after registration.

Three aggregates do this and they were three copies of the same loop: a model is
copied the review questionnaire, a Product is scaffolded its four RACI
accountabilities, an ML Application gets both. The shape never varied -- append one
``CollectionItemAdded`` per item, numbering the ids from one and stepping the
expected version each time -- so it is written once here.

Not in ``collections.py``: that module states it is pure, and this writes events.
"""
from __future__ import annotations

from typing import Any, Iterable

from src.database import append_event
from src.governance.collections import EVENT_ITEM_ADDED


def seed_items(*, aggregate_type: str, aggregate_id: str, collection: str,
               items: Iterable[dict[str, Any]], id_prefix: str, after_version: int,
               actor: str, reason: str, config=None) -> int:
    """Append ``items`` to ``collection``; return the version after the last one.

    Ids are ``<prefix>-001``, ``-002``, … in the order given, which is the order the
    record then shows them in. The caller passes the version the registration event
    landed on: each append steps it, because these events go in one at a time and
    each expects the log as the one before it left it.
    """
    version = after_version
    for index, fields in enumerate(items, start=1):
        append_event(
            aggregate_type=aggregate_type, aggregate_id=aggregate_id,
            event_type=EVENT_ITEM_ADDED,
            payload={"collection": collection, "item_id": f"{id_prefix}-{index:03d}",
                     **fields},
            actor=actor, reason=reason, expected_version=version, config=config)
        version += 1
    return version
