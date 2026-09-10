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
"""Proposing, ratifying and declining a division's lifecycle stage list.

The lifecycle is ``ratified_policy``; what is here is what makes a CHOICE valid, plus
the check that has to look outside it -- **a stage this division's records are in may
not be dropped**.

That check runs at propose time, with the rest, so a draft that would strand records
never reaches an agenda. Letting it through would spend a committee sitting on something
the machine could already see.

A division chooses VALUES from the catalogue; it does not author words. So there is
nothing to mint and nothing to name -- the shortest of the three ratified vocabularies,
and deliberately so.
"""
from __future__ import annotations

from dataclasses import replace
from typing import Any

from config.governance import LIFECYCLE_STAGE_FIELD
from src.database import Event
from src.governance.errors import DomainError
from src.governance.lifecycle_stage_catalogue import catalogue_values
from src.governance.lifecycle_stages._store import POLICY


def _validate_choice(policy: Any) -> None:
    """A division's list is an ordered array of catalogue values and nothing else."""
    if not isinstance(policy, list):
        raise DomainError(
            "a division lifecycle stage list must be an array of catalogue values")
    if not policy:
        raise DomainError(
            "a division must use at least one lifecycle stage -- ratifying none would "
            "be indistinguishable from having ratified nothing, which already means "
            "the whole catalogue")
    catalogue = catalogue_values()
    seen: set[str] = set()
    for entry in policy:
        if not isinstance(entry, str):
            raise DomainError(
                "each lifecycle stage must be a catalogue value, written as text")
        value = entry.strip()
        if not value:
            raise DomainError("a lifecycle stage cannot be blank")
        if value not in catalogue:
            raise DomainError(
                f"{value} is not in the institution's lifecycle stage catalogue -- a "
                f"division chooses from it rather than adding to it. It offers: "
                f"{', '.join(catalogue)}")
        if value in seen:
            raise DomainError(f"lifecycle stage {value} is chosen twice")
        seen.add(value)


_POLICY = replace(POLICY, validate=_validate_choice)


def stages_in_use(division: str, config=None) -> dict[str, list[str]]:
    """``{stage: [record ids]}`` for one division, across the three registers.

    Read twice: by ``_reject_removals_in_use`` below, and by the Admin editor, which
    shows the count beside each stage so a committee sees what dropping one would cost
    before it tries rather than as a refusal afterwards.

    The registers validate against this package, so importing them at module scope would
    close a cycle; they are imported here instead. Live records only, and a Product is
    absent because it carries a status rather than a stage -- both as the catalogue's
    own ``stages_in_use`` has it.
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
            data = row.get("data") or {}
            if data.get("division") != division:
                continue
            held = str(data.get(LIFECYCLE_STAGE_FIELD) or "").strip()
            if held:
                in_use.setdefault(held, []).append(str(row.get(id_key)))
    return in_use


def _reject_removals_in_use(division: str, stages: Any, config) -> None:
    """Refuse a proposal that drops a stage this division's records are in."""
    if not isinstance(stages, list):
        return
    proposed = {s.strip() for s in stages if isinstance(s, str)}
    for value, records in sorted(stages_in_use(division, config).items()):
        if value in proposed:
            continue
        held_by = ", ".join(sorted(records))
        raise DomainError(
            f"lifecycle stage {value} cannot be dropped while {len(records)} of this "
            f"division's record(s) are in it: {held_by}")


def propose_division_stages(*, division: str, stages: Any, actor: str,
                            reason: str | None = None, config=None) -> Event:
    """Submit a division's draft stage list for its MRC's sign-off.

    Nothing on any record changes until it is approved: a draft is a proposal about the
    stages the division will use, not a change to the ones it uses today.
    """
    stripped = [s.strip() if isinstance(s, str) else s for s in stages] \
        if isinstance(stages, list) else stages
    _reject_removals_in_use(division, stripped, config)
    return _POLICY.propose(scope=division, policy=stripped, actor=actor, reason=reason,
                           config=config)


def approve_division_stages(*, division: str, actor: str, meeting_id: str | None = None,
                            reason: str | None = None, config=None) -> Event:
    """Ratify the pending draft: it becomes the stages this division's records use."""
    return _POLICY.approve(scope=division, actor=actor, meeting_id=meeting_id,
                           reason=reason, config=config)


def reject_division_stages(*, division: str, actor: str, meeting_id: str | None = None,
                           reason: str | None = None, config=None) -> Event:
    """Decline or withdraw the pending draft. The live list is unchanged."""
    return _POLICY.reject(scope=division, actor=actor, meeting_id=meeting_id,
                          reason=reason, config=config)
