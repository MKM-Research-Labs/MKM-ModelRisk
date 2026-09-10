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
"""Proposing, ratifying and declining a division's functional group list.

The lifecycle is ``ratified_policy``; what is here is what makes a LIST valid, plus
the one check that has to look outside the policy -- **a group a record still holds
may not be removed**.

That check runs at propose time, with the rest, so a draft that would orphan
records never reaches an agenda. Letting it through instead would spend a committee
sitting on something the machine could already see, and the committee would be
refusing on a technicality rather than on judgement.

Ids are minted here rather than by the editor. A client that invents its own would
have to know the numbering rule, and two administrators drafting at once would
invent the same one. They are minted **per division**, so PhysicalRisk and Analytics
both have an FG-001 and they are different groups -- which is why a record may not
carry its group across a division change (``_validate.reject_division_move_while_grouped``).
"""
from __future__ import annotations

from dataclasses import replace
from typing import Any

from config.governance import (FUNCTIONAL_GROUP_FIELD, FUNCTIONAL_GROUP_ID_PREFIX,
                               FUNCTIONAL_GROUP_KEYS)
from src.database import Event
from src.governance.collections import next_item_id
from src.governance.errors import DomainError
from src.governance.functional_groups._store import POLICY


def _validate_groups(policy: Any) -> None:
    """A list is an ordered array of ``{id, name, description}`` and nothing else.

    Names are compared case-insensitively and stripped: two groups a reader cannot
    tell apart are not two groups, and a committee should never be asked to ratify
    a list with "Flood Simulation" twice in it.
    """
    if not isinstance(policy, list):
        raise DomainError("a functional group list must be an array of groups")
    seen_ids: set[str] = set()
    seen_names: set[str] = set()
    for entry in policy:
        if not isinstance(entry, dict):
            raise DomainError("each functional group must be an object")
        unknown = sorted(set(entry) - set(FUNCTIONAL_GROUP_KEYS))
        if unknown:
            raise DomainError(
                f"unknown functional group key(s): {', '.join(unknown)} -- "
                f"expected {', '.join(FUNCTIONAL_GROUP_KEYS)}")
        group_id = str(entry.get("id") or "").strip()
        name = str(entry.get("name") or "").strip()
        if not group_id:
            raise DomainError("each functional group needs an id")
        if not name:
            raise DomainError(f"functional group {group_id} needs a name")
        if group_id in seen_ids:
            raise DomainError(f"functional group id {group_id} is used twice")
        if name.casefold() in seen_names:
            raise DomainError(f"two functional groups are both named '{name}'")
        seen_ids.add(group_id)
        seen_names.add(name.casefold())


_POLICY = replace(POLICY, validate=_validate_groups)


def _mint_ids(groups: Any) -> Any:
    """Give every group without an id the next one, leaving existing ids alone.

    Garbage passes through untouched so that ``_validate_groups`` is what refuses
    it, with a message about the actual problem rather than a ``TypeError`` raised
    while trying to number it.
    """
    if not isinstance(groups, list) or not all(isinstance(g, dict) for g in groups):
        return groups
    # Strings are stripped as they are taken in, not only as they are checked:
    # validation compares a stripped id, so storing the padded one would leave a
    # group whose id passed every check and matches nothing on a record.
    minted = [{k: v.strip() if isinstance(v, str) else v for k, v in group.items()}
              for group in groups]
    for group in minted:
        if str(group.get("id") or "").strip():
            continue
        # ``next_item_id`` numbers one past the highest in use rather than from the
        # count, which is what stops a removed group's number being reissued to a
        # different group. It reads ``item_id``, so the ids in play are handed to it
        # under that name.
        group["id"] = next_item_id([{"item_id": g.get("id")} for g in minted],
                                   FUNCTIONAL_GROUP_ID_PREFIX)
    return minted


def groups_in_use(division: str, config=None) -> dict[str, list[str]]:
    """``{group id: [record ids]}`` across the four registers, for one division.

    Read twice: by ``_reject_removals_in_use`` below, and by the Admin editor, which
    shows the count beside each group so an administrator sees what a removal would
    cost before attempting it rather than as a refusal afterwards.

    The registers validate a record's group against this package, so importing them
    at module scope would close a cycle; they are imported here instead, as
    ``reference/_validate`` does for the same reason.

    Live records only. A hibernated record is out of every estate-wide figure by the
    same rule ``list_models`` states, and blocking a committee from tidying its list
    because of a record nobody is ever going to complete is a poor trade. An id held
    by a record the policy no longer defines resolves to nothing and shows as
    ungrouped, which is the right outcome for one that has been out of the estate
    for years.
    """
    from src.governance.ai_system import list_ai_systems
    from src.governance.ml_application import list_ml_applications
    from src.governance.model_inventory import list_models
    from src.governance.product import list_products

    registers = ((list_models(config), "model_id"),
                 (list_products(config), "product_id"),
                 (list_ml_applications(config), "ml_application_id"),
                 (list_ai_systems(config), "ai_system_id"))
    in_use: dict[str, list[str]] = {}
    for rows, id_key in registers:
        for row in rows:
            if row.get("retired"):
                continue
            data = row.get("data") or {}
            if data.get("division") != division:
                continue
            held = str(data.get(FUNCTIONAL_GROUP_FIELD) or "").strip()
            if held:
                in_use.setdefault(held, []).append(str(row.get(id_key)))
    return in_use


def _reject_removals_in_use(division: str, groups: Any, config) -> None:
    """Refuse a proposal that drops a group records in this division still hold.

    Compared against what the ESTATE holds rather than against the live policy, so
    the answer is the same whether or not a draft is already outstanding: whatever a
    record is filed under has to survive the proposal.
    """
    if not isinstance(groups, list):
        return
    proposed = {str(g.get("id") or "").strip()
                for g in groups if isinstance(g, dict)}
    for group_id, records in sorted(groups_in_use(division, config).items()):
        if group_id in proposed:
            continue
        held_by = ", ".join(sorted(records))
        raise DomainError(
            f"functional group {group_id} cannot be removed while "
            f"{len(records)} record(s) are filed under it: {held_by}")


def propose_functional_groups(*, division: str, groups: Any, actor: str,
                              reason: str | None = None, config=None) -> Event:
    """Submit a division's draft functional group list for MRC sign-off.

    Nothing on any record changes until it is approved: a draft is a proposal about
    how the estate will be carved up, not a change to how it is carved up today.
    """
    minted = _mint_ids(groups)
    _reject_removals_in_use(division, minted, config)
    return _POLICY.propose(scope=division, policy=minted, actor=actor,
                           reason=reason, config=config)


def approve_functional_groups(*, division: str, actor: str,
                              meeting_id: str | None = None,
                              reason: str | None = None, config=None) -> Event:
    """Ratify the pending draft: it becomes the list records are assigned from."""
    return _POLICY.approve(scope=division, actor=actor, meeting_id=meeting_id,
                           reason=reason, config=config)


def reject_functional_groups(*, division: str, actor: str,
                             meeting_id: str | None = None,
                             reason: str | None = None, config=None) -> Event:
    """Decline or withdraw the pending draft. The live list is unchanged."""
    return _POLICY.reject(scope=division, actor=actor, meeting_id=meeting_id,
                          reason=reason, config=config)
