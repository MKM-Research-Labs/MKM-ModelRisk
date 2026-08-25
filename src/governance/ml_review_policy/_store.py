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
"""ML review policy store: what a division's ML review asks for, MRC-ratified.

Same lifecycle as the risk policy and the same module runs it -- Proposed → Approved
/ Rejected, per division, in ``ratified_policy``. What is specific here is the
*catalogue*: the list of things that can be asked for, which is half static (the
training fields, defined in code) and half the institution's own (the review
questions, a reference list it edits).

That split is why the catalogue is assembled here rather than in config. The training
half is pure data; the question half is a read.
"""
from __future__ import annotations

from typing import Any

from config.governance import (ML_APPLICATION_QUESTION_LIST,
                               ML_REVIEW_POLICY_AGGREGATE, ML_REVIEW_POLICY_NOUN,
                               QUESTION_GROUP_KEY, QUESTION_ITEM_SOURCE,
                               TRAINING_ITEM_SOURCE, default_review_policy,
                               policy_item_id, resolve_item, training_policy_items)
from src.governance.ratified_policy import RatifiedPolicy
from src.governance.reference import get_reference_lists

POLICY = RatifiedPolicy(aggregate_type=ML_REVIEW_POLICY_AGGREGATE,
                        noun=ML_REVIEW_POLICY_NOUN, default=default_review_policy)

AGGREGATE_TYPE = ML_REVIEW_POLICY_AGGREGATE


def question_policy_items(config=None) -> list[dict[str, Any]]:
    """The institution's review questions as reviewable items.

    Read at call time, never cached: a question added in Admin is askable straight
    away, resolving to the default until somebody says otherwise.
    """
    rows = (get_reference_lists(config=config) or {}).get(ML_APPLICATION_QUESTION_LIST) or []
    items = []
    for row in rows:
        # Keyed by TOPIC, not by the register row's id. A record's copy of a question
        # is seeded with an id of its own (``VQ-003``), so an id join would never
        # match; ``short_label`` is what the register already treats as the row's
        # identity and what the record copies verbatim. Renaming a topic in Admin
        # therefore strands its policy entry -- which resolves to the default and does
        # nothing, the same as any other stale entry.
        key = row.get("short_label") or ""
        if not key:
            continue
        items.append({"item_id": policy_item_id(QUESTION_ITEM_SOURCE, key),
                      "source": QUESTION_ITEM_SOURCE, "key": key,
                      "group": QUESTION_GROUP_KEY,
                      "label": row.get("short_label") or key,
                      "note": row.get("question") or ""})
    return items


def catalogue(config=None) -> list[dict[str, Any]]:
    """Everything an ML review could ask for: training fields, then questions."""
    return list(training_policy_items()) + question_policy_items(config)


def load(division: str, config=None) -> dict:
    """Fold a division's stream into ``{live, draft, state, approved, version}``."""
    return POLICY.load(division, config)


def get_ml_review_policy(division: str, config=None) -> dict:
    """The LIVE policy a division's ML Applications are reviewed against."""
    return POLICY.live(division, config)


def get_ml_review_policy_draft(division: str, config=None) -> dict | None:
    """The division's proposed policy awaiting MRC sign-off, or None."""
    return POLICY.draft(division, config)


def resolved_policy(division: str, config=None,
                    policy: dict | None = None) -> dict[str, dict[str, bool]]:
    """Every catalogue item's effective setting for ``division``.

    ``policy`` overrides the live one, so the admin editor can show what a *draft*
    would do without ratifying it first.
    """
    live = policy if policy is not None else get_ml_review_policy(division, config)
    return {item["item_id"]: resolve_item(live, item["item_id"])
            for item in catalogue(config)}


def _keys_where(division: str, source: str, flag: str, config,
                policy: dict | None) -> tuple[str, ...]:
    resolved = resolved_policy(division, config, policy)
    return tuple(item["key"] for item in catalogue(config)
                 if item["source"] == source and resolved[item["item_id"]][flag])


def in_use_keys(division: str, source: str = TRAINING_ITEM_SOURCE, config=None,
                policy: dict | None = None) -> tuple[str, ...]:
    """The keys of ``source`` this division shows -- the screens' list."""
    return _keys_where(division, source, "in_use", config, policy)


def mandatory_keys(division: str, source: str = TRAINING_ITEM_SOURCE, config=None,
                   policy: dict | None = None) -> tuple[str, ...]:
    """The keys of ``source`` this division requires before a review can complete."""
    return _keys_where(division, source, "mandatory", config, policy)
