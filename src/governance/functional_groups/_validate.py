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
"""Validation of a record's functional group against its division's ratified list.

Shared by every register that carries the field -- the model inventory, Products,
ML Applications and AI Systems. Held here rather than in each aggregate's rules
because the allowed values are a division's ratified policy, so this is that
policy's business and not the inventory's. Four copies would drift the moment one
of them learned something the others did not, which is exactly what happened to the
four ``/fields`` handlers before ``grouped_field_specs`` gathered them.
"""
from __future__ import annotations

from typing import Any

from config.governance import FUNCTIONAL_GROUP_FIELD
from src.governance.errors import DomainError
from src.governance.functional_groups._store import group_names


def reject_unknown_functional_group(value: Any, division: Any, config=None) -> None:
    """Refuse a group the division's MRC has not ratified.

    **Blank passes.** A record must be able to hold no group at all: before its
    division has ratified a list, and afterwards when somebody takes it out of one.
    The risk fields refuse a blank because a model must always carry a rating; a
    functional group is a filing decision and "not filed yet" is a real answer.

    The refusal names the groups rather than their ids, because a person reads it
    and "must be one of: FG-001, FG-002" tells them nothing.
    """
    if not str(value or "").strip():
        return
    names = group_names(division or "", config)
    if not names:
        raise DomainError(
            f"{division or 'this division'} has no ratified functional groups -- "
            "its MRC has to sign a list off before a record can be filed under one")
    if value not in names:
        allowed = ", ".join(f"{name} ({group_id})" for group_id, name in names.items())
        raise DomainError(f"functional group must be one of: {allowed}")


def reject_division_move_while_grouped(fields: dict, new_division: Any) -> None:
    """Refuse to move a record out of the division whose group it is filed under.

    Ids are minted per division, so PhysicalRisk and Analytics both have an FG-001
    and they are different groups. A record carried across with its group still set
    would therefore not be left holding a DANGLING reference, which a screen could
    at least show as ungrouped -- it would silently acquire the new division's group
    of the same number. Nothing about the record would look wrong, and it would be
    counted, filtered and reported under a group nobody filed it in.

    So the move is refused while a group is set. Clearing it first is one edit, and
    a division change is rare and consequential enough that being asked where the
    record now files is the right thing to be asked.
    """
    held = str((fields or {}).get(FUNCTIONAL_GROUP_FIELD) or "").strip()
    if not held or (fields or {}).get("division") == new_division:
        return
    raise DomainError(
        f"clear the functional group ({held}) before moving this record to "
        f"{new_division or 'no division'} -- groups are defined per division, so it "
        "would not carry across")
