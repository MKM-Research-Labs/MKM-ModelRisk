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
"""What an ML Application's review asks for: the shape of the institution's answer.

The platform proposes a catalogue -- 51 typed training fields across six sections,
plus the review questions -- and the institution says which of it applies. Two
independent ticks per item:

    in_use      the item is shown on the record's screens at all
    mandatory   the item must be filled before the review can be completed

Two ticks rather than one three-state control because an adopter sets them at
different times: switch things on to begin with, tighten later once people are
filling them in. ``mandatory`` implies ``in_use`` -- an item nobody is shown cannot
be one they are required to answer -- and that implication is enforced in the domain
rules, not left to a checkbox to remember.

**Everything in use, nothing mandatory** is the default, which is the position
settled in T6 and means an estate running today sees no change the day this ships.
Tightening is a deliberate act, made from a screen that shows what is being tightened
and ratified by the division's MRC.

No I/O here: the review questions are a reference list read at runtime, so this module
describes the training half and the *shape* of a policy, and ``ml_review_policy``
assembles the whole catalogue.
"""
from __future__ import annotations

from typing import Any

from config.governance._ml_training import TRAINING_FIELD_SPECS, TRAINING_SECTIONS

# Where a reviewable item comes from. Both halves are ticked the same way; only their
# origin differs, and an id carries it so the two can never collide (a training field
# key and a question's item id are both short strings).
TRAINING_ITEM_SOURCE = "training"
QUESTION_ITEM_SOURCE = "question"
ML_REVIEW_ITEM_SOURCES = (TRAINING_ITEM_SOURCE, QUESTION_ITEM_SOURCE)

# The aggregate the policy is stored under, and the noun its refusals use.
ML_REVIEW_POLICY_AGGREGATE = "MLReviewPolicy"
ML_REVIEW_POLICY_NOUN = "ML review policy"

# Group headings for the Admin tab: the training sections as they are already
# numbered on the Training tab, then the questions.
QUESTION_GROUP_KEY = "Q"
QUESTION_GROUP_LABEL = "Review questions"


def policy_item_id(source: str, key: str) -> str:
    """The stable id a policy is keyed by: ``training:learning_task``."""
    return f"{source}:{key}"


def split_item_id(item_id: str) -> tuple[str, str]:
    """``training:learning_task`` -> ``("training", "learning_task")``."""
    source, _, key = str(item_id).partition(":")
    return source, key


def training_policy_items() -> tuple[dict[str, Any], ...]:
    """Every training field as a reviewable item, in the order the tab shows them."""
    return tuple(
        {"item_id": policy_item_id(TRAINING_ITEM_SOURCE, key),
         "source": TRAINING_ITEM_SOURCE, "key": key,
         "group": spec["section"], "label": spec["label"],
         "note": spec.get("note", "")}
        for key, spec in TRAINING_FIELD_SPECS.items()
    )


def item_group_labels() -> dict[str, str]:
    """Group key -> heading, for the Admin tab and the record's sub-tabs."""
    labels = {key: title for key, title in TRAINING_SECTIONS}
    labels[QUESTION_GROUP_KEY] = QUESTION_GROUP_LABEL
    return labels


# One item's setting when the institution has said nothing about it. An item added to
# the catalogue after a policy was ratified -- a new review question, a training field
# we ship later -- resolves to this rather than vanishing from the screen or, worse,
# silently becoming mandatory.
DEFAULT_ITEM_POLICY = {"in_use": True, "mandatory": False}


def default_review_policy() -> dict[str, Any]:
    """The firm-wide seed: everything in use, nothing mandatory.

    Empty rather than a filled-in map, because "no override" and "explicitly set to
    the default" should not be different states -- resolution answers both.
    """
    return {}


def resolve_item(policy: dict | None, item_id: str) -> dict[str, bool]:
    """One item's effective setting, defaults applied.

    ``mandatory`` is read only where ``in_use`` holds, so a policy that somehow
    records a mandatory item that is switched off cannot make a record uncompletable
    against a field nobody can see.
    """
    stored = (policy or {}).get(item_id) or {}
    in_use = bool(stored.get("in_use", DEFAULT_ITEM_POLICY["in_use"]))
    mandatory = bool(stored.get("mandatory", DEFAULT_ITEM_POLICY["mandatory"]))
    return {"in_use": in_use, "mandatory": in_use and mandatory}
