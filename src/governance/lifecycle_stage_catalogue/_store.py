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
"""The institution's stage catalogue, as its Company MRC last ratified it.

The lifecycle is ``ratified_policy`` -- Proposed → Approved / Rejected -- and this
module is the reads on top of it. Two things are specific here: the policy IS the
vocabulary, so ``live`` is the ordered stages themselves; and it is a SINGLETON, one
document for the whole institution, so there is no scope to pass in.

Order is part of what was ratified. A committee that arranged the stages arranged them
for a reason -- "Pre Development" is first because a record starts there -- so every
dropdown offers them in that order rather than alphabetically.
"""
from __future__ import annotations

from config.governance import (LIFECYCLE_CATALOGUE_AGGREGATE, LIFECYCLE_CATALOGUE_NOUN,
                               LIFECYCLE_CATALOGUE_SCOPE, default_lifecycle_stages)
from src.governance.ratified_policy import RatifiedPolicy

# ``scope_noun=None`` marks the singleton: the refusals then read "there is no proposed
# lifecycle stage catalogue awaiting sign-off" rather than naming the fixed id it is
# stored under, which would tell a reader nothing.
POLICY = RatifiedPolicy(aggregate_type=LIFECYCLE_CATALOGUE_AGGREGATE,
                        noun=LIFECYCLE_CATALOGUE_NOUN,
                        default=default_lifecycle_stages,
                        scope_noun=None)

AGGREGATE_TYPE = LIFECYCLE_CATALOGUE_AGGREGATE


def load(config=None) -> dict:
    """Fold the catalogue stream into ``{live, draft, state, approved, version}``."""
    return POLICY.load(LIFECYCLE_CATALOGUE_SCOPE, config)


def get_catalogue(config=None) -> list[dict]:
    """The LIVE catalogue: every stage the institution recognises, in order.

    An institution that has ratified nothing gets the five the platform ships, which is
    what makes adopting this free of migration -- every record in the estate already
    carries one of those words.
    """
    return POLICY.live(LIFECYCLE_CATALOGUE_SCOPE, config)


def get_catalogue_draft(config=None) -> list[dict] | None:
    """The proposal awaiting the Company MRC's sign-off, or ``None``.

    Read by the Admin editor and by the meeting's sign-off item. It drives nothing: a
    stage that is only proposed is not one a record can be set to.
    """
    return POLICY.draft(LIFECYCLE_CATALOGUE_SCOPE, config)


def catalogue_values(config=None) -> tuple[str, ...]:
    """The values a record may hold, in catalogue order."""
    return tuple(stage["value"] for stage in get_catalogue(config) if stage.get("value"))


def catalogue_labels(config=None) -> dict[str, str]:
    """``{value: label}`` -- what a screen shows for what a record stores.

    A value with no label falls back to itself, so a half-written entry is visible as
    itself rather than as a blank cell.
    """
    return {stage["value"]: stage.get("label") or stage["value"]
            for stage in get_catalogue(config) if stage.get("value")}
