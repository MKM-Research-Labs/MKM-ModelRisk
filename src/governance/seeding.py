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


def _recorded_or_shipped(list_name: str, shipped, config) -> list[dict[str, str]]:
    """The institution's own version of a question list, or the shipped set.

    Falls back only where nothing has been recorded — a fresh database before the
    first-run seed, or a list somebody has emptied. Written once here because the ML
    Application and the AI System each had a copy of it, and a third was about to be
    written for the common list.
    """
    from src.governance.reference import get_reference_lists
    try:
        recorded = get_reference_lists(config=config).get(list_name) or []
    except Exception:
        recorded = []
    asked = [{"short_label": q.get("short_label") or "", "question": q.get("question") or ""}
             for q in recorded if (q.get("question") or "").strip()]
    return asked or [dict(q) for q in shipped]


def compose_questions(own_list: str, own_shipped, config=None) -> list[dict[str, str]]:
    """The questionnaire a record is asked: the common questions, then its own.

    **The order is part of the contract.** Common first, always: a reviewer opening any
    record meets the same five questions in the same order, whatever kind of thing it
    is, and a report comparing two record types compares row 1 with row 1.

    The result is ONE flat list. Nothing downstream is told the questions came from two
    places — the record carries a single questionnaire, its items numbered from one, and
    the review works through them without knowing or caring where each was authored.
    That is what lets the split happen without touching the review, the completeness
    probes or the sign-off pack.

    A record keeps what it was given. Editing either list afterwards never rewrites an
    answer already recorded, which is why each record is copied its own snapshot.
    """
    from config.governance._questions_common import (COMMON_QUESTION_LIST,
                                                     COMMON_QUESTIONS)
    return (_recorded_or_shipped(COMMON_QUESTION_LIST, COMMON_QUESTIONS, config)
            + _recorded_or_shipped(own_list, own_shipped, config))


__all__ = ["compose_questions", "seed_items"]
