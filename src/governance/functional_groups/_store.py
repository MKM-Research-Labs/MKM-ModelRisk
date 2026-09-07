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
"""Functional-group store: one division's list, as the MRC last ratified it.

The lifecycle is ``ratified_policy`` -- Proposed → Approved / Rejected, per
division -- and this module is the reads on top of it. What is specific here is
that the policy IS the list: there is no catalogue to resolve a setting against and
no per-item flags, so ``live`` is the ordered groups themselves.

Order is part of the policy and is preserved everywhere it is read. A committee
that arranged its list arranged it for a reason, so the register screens group in
that order rather than alphabetically.
"""
from __future__ import annotations

from config.governance import (FUNCTIONAL_GROUPS_AGGREGATE, FUNCTIONAL_GROUPS_NOUN,
                               default_functional_groups)
from src.governance.ratified_policy import RatifiedPolicy

POLICY = RatifiedPolicy(aggregate_type=FUNCTIONAL_GROUPS_AGGREGATE,
                        noun=FUNCTIONAL_GROUPS_NOUN,
                        default=default_functional_groups)

AGGREGATE_TYPE = FUNCTIONAL_GROUPS_AGGREGATE


def load(division: str, config=None) -> dict:
    """Fold a division's stream into ``{live, draft, state, approved, version}``."""
    return POLICY.load(division, config)


def get_functional_groups(division: str, config=None) -> list[dict]:
    """The LIVE groups a record in ``division`` may be assigned to.

    A division that has never ratified a list gets the empty default, which is the
    honest answer: its records may hold no group at all until its committee has
    said what the groups are.
    """
    return POLICY.live(division, config)


def get_functional_groups_draft(division: str, config=None) -> list[dict] | None:
    """The division's proposed list awaiting MRC sign-off, or ``None``.

    Read by the Admin editor and by the meeting's sign-off item. It drives nothing:
    a record cannot be assigned to a group that is only proposed.
    """
    return POLICY.draft(division, config)


def group_ids(division: str, config=None) -> tuple[str, ...]:
    """The ids a record in ``division`` may hold, in policy order."""
    return tuple(group["id"] for group in get_functional_groups(division, config)
                 if group.get("id"))


def group_names(division: str, config=None) -> dict[str, str]:
    """``{id: name}`` for ``division`` -- what a screen shows for what a record stores.

    An id with no name falls back to the id, so a half-written entry is visible as
    itself rather than as a blank cell.
    """
    return {group["id"]: group.get("name") or group["id"]
            for group in get_functional_groups(division, config) if group.get("id")}
