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
"""Proposing, ratifying and declining the institution's stage catalogue.

The lifecycle is ``ratified_policy``; what is here is what makes a CATALOGUE valid,
plus the two checks that have to look outside it -- **a stage a record still holds may
not be removed**, and **a value may not change once it exists**.

Both run at propose time, with the rest, so a draft that would orphan records never
reaches an agenda. Letting one through instead would spend a committee sitting on
something the machine could already see, and the committee would be refusing on a
technicality rather than on judgement.

Shaped on ``functional_groups.commands``, which is the same journey for a per-division
list. What differs is that a stage carries no minted id -- the ``value`` IS the key,
seeded to the word records already carry, so the entries are authored rather than
numbered.
"""
from __future__ import annotations

from dataclasses import replace
from typing import Any

from config.governance import (LIFECYCLE_CATALOGUE_SCOPE, LIFECYCLE_STAGE_FIELD,
                               LIFECYCLE_STAGE_KEYS)
from src.database import Event
from src.governance.errors import DomainError
from src.governance.lifecycle_stage_catalogue._store import POLICY, get_catalogue

def _validate_catalogue(policy: Any) -> None:
    """A catalogue is an ordered array of ``{value, label, description}`` and nothing else.

    Values and labels are both compared case-insensitively and stripped: two stages a
    reader cannot tell apart are not two stages, and a committee should never be asked
    to ratify a list with "Production" twice in it.
    """
    if not isinstance(policy, list):
        raise DomainError("a lifecycle stage catalogue must be an array of stages")
    if not policy:
        raise DomainError(
            "a lifecycle stage catalogue cannot be empty -- every record in the estate "
            "carries a stage, and there would be none left to carry")
    seen_values: set[str] = set()
    seen_labels: set[str] = set()
    for entry in policy:
        if not isinstance(entry, dict):
            raise DomainError("each lifecycle stage must be an object")
        unknown = sorted(set(entry) - set(LIFECYCLE_STAGE_KEYS))
        if unknown:
            raise DomainError(
                f"unknown lifecycle stage key(s): {', '.join(unknown)} -- "
                f"expected {', '.join(LIFECYCLE_STAGE_KEYS)}")
        value = str(entry.get("value") or "").strip()
        label = str(entry.get("label") or "").strip()
        if not value:
            raise DomainError("each lifecycle stage needs a stored value")
        if not label:
            raise DomainError(f"lifecycle stage {value} needs a label")
        if value.casefold() in seen_values:
            raise DomainError(f"lifecycle stage value {value} is used twice")
        if label.casefold() in seen_labels:
            raise DomainError(f"two lifecycle stages are both shown as '{label}'")
        seen_values.add(value.casefold())
        seen_labels.add(label.casefold())


_POLICY = replace(POLICY, validate=_validate_catalogue)


def stages_in_use(config=None) -> dict[str, list[str]]:
    """``{stage value: [record ids]}`` across every register that carries a stage.

    Read twice: by ``_reject_removals_in_use`` below, and by the Admin editor, which
    shows the count beside each stage so an administrator sees what a removal would cost
    before attempting it rather than as a refusal afterwards.

    The registers validate a record's stage against this package, so importing them at
    module scope would close a cycle; they are imported here instead, as
    ``functional_groups.commands`` and ``reference/_validate`` do for the same reason.

    A Product is not here: it carries a ``status``, not a lifecycle stage.

    Live records only. A hibernated record is out of every estate-wide figure by the
    same rule ``list_models`` states, and blocking a committee from tidying its
    vocabulary because of a record nobody is ever going to complete is a poor trade.
    """
    from src.governance.ai_system import list_ai_systems
    from src.governance.ml_application import list_ml_applications
    from src.governance.model_inventory import list_models

    registers = ((list_models(config), "model_id"),
                 (list_ml_applications(config), "ml_application_id"),
                 (list_ai_systems(config), "ai_system_id"))
    in_use: dict[str, list[str]] = {}
    for rows, id_key in registers:
        for row in rows:
            if row.get("retired"):
                continue
            held = str((row.get("data") or {}).get(LIFECYCLE_STAGE_FIELD) or "").strip()
            if held:
                in_use.setdefault(held, []).append(str(row.get(id_key)))
    return in_use


def _reject_removals_in_use(stages: Any, config) -> None:
    """Refuse a proposal that drops a stage records in the estate still hold.

    Compared against what the ESTATE holds rather than against the live catalogue, so
    the answer is the same whether or not a draft is already outstanding: whatever a
    record carries has to survive the proposal.
    """
    if not isinstance(stages, list):
        return
    proposed = {str(s.get("value") or "").strip()
                for s in stages if isinstance(s, dict)}
    for value, records in sorted(stages_in_use(config).items()):
        if value in proposed:
            continue
        held_by = ", ".join(sorted(records))
        raise DomainError(
            f"lifecycle stage {value} cannot be removed while {len(records)} "
            f"record(s) are in it: {held_by}")


def _reject_value_edits(stages: Any, config) -> None:
    """Refuse a proposal that RENAMES a stored value.

    A value is what records carry, so editing one orphans every record in that stage
    silently -- the record keeps a word the catalogue no longer defines. Renaming is
    what the ``label`` is for, and it moves nothing.

    Matched by position rather than by identity, because a value IS the identity: an
    entry whose value has changed is indistinguishable from one removed and another
    added, and the removal check above already covers a value the estate is using. What
    this adds is the case nothing holds yet, where a silent rename would otherwise pass.
    """
    if not isinstance(stages, list):
        return
    live = {str(stage.get("value") or "").strip() for stage in get_catalogue(config)}
    if not live:
        return
    proposed = {str(s.get("value") or "").strip()
                for s in stages if isinstance(s, dict)}
    for gone in sorted(live - proposed):
        near = sorted(p for p in proposed - live if p.casefold() == gone.casefold())
        if near:
            raise DomainError(
                f"a stored value cannot be changed once set: {gone} -> {near[0]}. "
                "Records carry the value; edit the label instead, which moves nothing.")


def propose_lifecycle_catalogue(*, stages: Any, actor: str, reason: str | None = None,
                                config=None) -> Event:
    """Submit a draft catalogue for the Company MRC's sign-off.

    Nothing on any record changes until it is approved: a draft is a proposal about the
    words the institution will recognise, not a change to the words it recognises today.
    """
    stripped = _strip(stages)
    _reject_value_edits(stripped, config)
    _reject_removals_in_use(stripped, config)
    return _POLICY.propose(scope=LIFECYCLE_CATALOGUE_SCOPE, policy=stripped, actor=actor,
                           reason=reason, config=config)


def approve_lifecycle_catalogue(*, actor: str, meeting_id: str | None = None,
                                reason: str | None = None, config=None) -> Event:
    """Ratify the pending draft: it becomes the vocabulary divisions choose from."""
    return _POLICY.approve(scope=LIFECYCLE_CATALOGUE_SCOPE, actor=actor,
                           meeting_id=meeting_id, reason=reason, config=config)


def reject_lifecycle_catalogue(*, actor: str, meeting_id: str | None = None,
                               reason: str | None = None, config=None) -> Event:
    """Decline or withdraw the pending draft. The live catalogue is unchanged."""
    return _POLICY.reject(scope=LIFECYCLE_CATALOGUE_SCOPE, actor=actor,
                          meeting_id=meeting_id, reason=reason, config=config)


def _strip(stages: Any) -> Any:
    """Strip every string as it is taken in, not only as it is checked.

    Validation compares a stripped value, so storing the padded one would leave a stage
    that passed every check and matches nothing on a record. Garbage passes through
    untouched so that ``_validate_catalogue`` is what refuses it, with a message about
    the actual problem rather than a ``TypeError`` raised while tidying it.
    """
    if not isinstance(stages, list) or not all(isinstance(s, dict) for s in stages):
        return stages
    return [{k: v.strip() if isinstance(v, str) else v for k, v in stage.items()}
            for stage in stages]
