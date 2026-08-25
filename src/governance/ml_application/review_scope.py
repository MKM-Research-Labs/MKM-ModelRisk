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
"""One record's review, scoped to what its division actually asks for.

Resolved when a record is READ, never stored on it. A policy the committee ratifies
this morning applies to every record this afternoon without a view rebuild -- and a
figure baked into a read model is a figure that goes quietly stale the moment the
standard behind it moves.

The same answer serves three callers, which is why it is one function: the screens
(what to show, what to mark red), the completion gate (what may not be blank), and
the estate dashboard (how many records are short).
"""
from __future__ import annotations

from typing import Any

from config.governance._review import SIGNED_OFF_REVIEW_STATUS
from config.governance import (ML_REVIEW_QUESTIONS_COLLECTION, QUESTION_ITEM_SOURCE,
                               TRAINING_ITEM_SOURCE, TRAINING_RUNS_COLLECTION,
                               policy_item_id, resolve_item)
from src.governance.errors import DomainError
from src.governance.ml_application.training import completeness
from src.governance.ml_review_policy import (get_ml_review_policy, in_use_keys,
                                             mandatory_keys)  # noqa: F401

# A question counts as answered once it has been addressed. The status vocabulary is
# admin-managed, so what is checked is that a status was RECORDED and is not the
# not-yet word -- not equality with a status we happen to ship.
_UNADDRESSED = "Not Addressed"


def _answered(question: dict) -> bool:
    status = str(question.get("status") or "").strip()
    return bool(status) and status != _UNADDRESSED


def division_scope(division: str, config=None, cache: dict | None = None) -> dict:
    """The policy pieces one division needs, resolved once.

    Every read of these walks the catalogue, which reads the question register. Doing
    that per record turns an estate listing into one register read per row, so callers
    with more than one record pass a ``cache`` and pay for each division once.
    """
    if cache is not None and division in cache:
        return cache[division]
    resolved = {
        "train_in_use": set(in_use_keys(division, TRAINING_ITEM_SOURCE, config)),
        "train_required": mandatory_keys(division, TRAINING_ITEM_SOURCE, config),
        "policy": get_ml_review_policy(division, config),
    }
    if cache is not None:
        cache[division] = resolved
    return resolved


def review_scope(data: dict, config=None, cache: dict | None = None) -> dict[str, Any]:
    """What this record's division asks of it, and how far it has got.

    ``missing_mandatory`` names the items rather than counting them: a refusal that
    says "3 items outstanding" sends somebody hunting through six sub-tabs.
    """
    division = str(data.get("division") or "")
    resolved = division_scope(division, config, cache)
    train_in_use = resolved["train_in_use"]
    train_required = resolved["train_required"]
    policy = resolved["policy"]

    runs = data.get(TRAINING_RUNS_COLLECTION) or []
    training = completeness(runs[-1] if runs else None,
                            in_use=train_in_use, mandatory=train_required)

    # Resolved per question rather than filtered against the register, so a question
    # the register does not list -- a record migrated from a model carries the MODEL's
    # questions -- is shown rather than silently dropped off its own review. Unknown
    # resolves to the default: asked, not required.
    def _setting(question):
        return resolve_item(policy, policy_item_id(QUESTION_ITEM_SOURCE,
                                                   _question_key(question)))

    asked = [q for q in (data.get(ML_REVIEW_QUESTIONS_COLLECTION) or [])
             if _setting(q)["in_use"]]
    answered = [q for q in asked if _answered(q)]
    missing_questions = [_question_label(q) for q in asked
                         if _setting(q)["mandatory"] and not _answered(q)]

    return {
        "training": training,
        "questions": {"answered": len(answered), "total": len(asked),
                      "mandatory_total": len(
                          [q for q in asked if _setting(q)["mandatory"]]),
                      "missing_mandatory": missing_questions},
        # The screens filter on these; the record keeps everything it ever recorded.
        "training_in_use": sorted(train_in_use),
        "training_mandatory": list(train_required),
        "question_in_use": [_question_key(q) for q in asked],
        # Built from THIS RECORD's questions, not from the register's catalogue. A
        # question the register does not list is still resolved and still enforced, so
        # deriving the screen's list from the catalogue instead would enforce a
        # requirement the screen never marked -- refused at the gate, with nothing on
        # the page to say why.
        "question_mandatory": [_question_key(q) for q in asked
                               if _setting(q)["mandatory"]],
        "missing_mandatory": list(training["missing_mandatory"]) + missing_questions,
    }


def _question_key(question: dict) -> str:
    """A record's copy of a question is matched to the register by item_id.

    The TOPIC is the join: a record's copy is seeded with an id of its own, so the
    register's id is not on it to match against.
    """
    return str(question.get("short_label") or "")


def _question_label(question: dict) -> str:
    return str(question.get("short_label") or _question_key(question))


def is_complete(data: dict, config=None, cache: dict | None = None) -> bool:
    """Whether every mandatory item this record's division requires is filled."""
    return not review_scope(data, config, cache)["missing_mandatory"]


def review_status(data: dict, config=None, cache: dict | None = None) -> dict[str, Any]:
    """The compact form an estate listing needs: complete or not, and how short.

    Deliberately not the whole scope -- a list of two hundred records does not want
    two hundred copies of the catalogue in its payload.
    """
    scope = review_scope(data, config, cache)
    outstanding = scope["missing_mandatory"]
    return {"complete": not outstanding, "outstanding": len(outstanding),
            "required": (scope["training"]["mandatory_total"]
                         + scope["questions"]["mandatory_total"])}


# Setting the review to this is what "completing" it means: the record is being
# declared reviewed. Everything short of that -- recording evidence, answering a
# question, starting a train -- is work in progress and is never blocked.
COMPLETING_REVIEW_STATUS = SIGNED_OFF_REVIEW_STATUS
REVIEW_STATUS_FIELD = "review_status"


def guard_review_complete(data: dict, what: str, config=None) -> None:
    """Refuse to complete a review while the division's mandatory items are blank.

    The refusal NAMES what is outstanding. A gate that says "3 items missing" makes
    somebody open six sub-tabs to find them, and a gate people resent is a gate that
    gets switched off.

    Only completion is gated. A train can always be recorded and edited with mandatory
    fields empty: a barrier to writing evidence down is a barrier to evidence.
    """
    outstanding = review_scope(data, config)["missing_mandatory"]
    if outstanding:
        raise DomainError(
            f"{what} is not possible yet: this division's ML review policy requires "
            f"{len(outstanding)} item(s) that are still blank — "
            + ", ".join(outstanding))
