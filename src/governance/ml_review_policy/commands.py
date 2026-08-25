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
"""Proposing, ratifying and declining a division's ML review policy.

The lifecycle is ``ratified_policy``; what is here is what makes an ML REVIEW policy
valid. Validation runs at propose time so a broken policy never reaches a committee.
"""
from __future__ import annotations

from dataclasses import replace
from typing import Any

from config.governance import ML_REVIEW_ITEM_SOURCES, split_item_id
from src.database import Event
from src.governance.errors import DomainError
from src.governance.ml_review_policy._store import POLICY

_FLAGS = ("in_use", "mandatory")


def _validate_policy(policy: Any) -> None:
    """A policy is ``{item_id: {in_use: bool, mandatory: bool}}``, and nothing else.

    Unknown item ids are NOT rejected. A question can be deleted in Admin after the
    policy naming it was ratified, and refusing the whole policy because one entry has
    gone stale would make the committee re-ratify to fix somebody else's tidying. A
    stale entry resolves against a catalogue that no longer lists it, which is to say
    it does nothing.
    """
    if not isinstance(policy, dict):
        raise DomainError("an ML review policy must be an object of item settings")
    for item_id, setting in policy.items():
        source, key = split_item_id(item_id)
        if source not in ML_REVIEW_ITEM_SOURCES or not key:
            raise DomainError(
                f"'{item_id}' is not a reviewable item id: expected one of "
                f"{', '.join(ML_REVIEW_ITEM_SOURCES)} followed by ':' and a key")
        if not isinstance(setting, dict):
            raise DomainError(f"the setting for '{item_id}' must be an object")
        for flag in _FLAGS:
            if flag in setting and not isinstance(setting[flag], bool):
                raise DomainError(f"'{item_id}.{flag}' must be true or false")
        # Enforced here as well as in ``resolve_item`` so the stored policy says what
        # it means: a committee should never ratify a document that reads "required,
        # and not shown to anybody".
        if setting.get("mandatory") and not setting.get("in_use", True):
            raise DomainError(
                f"'{item_id}' cannot be mandatory while it is not in use -- an item "
                "nobody is shown cannot be one they are required to answer")


_POLICY = replace(POLICY, validate=_validate_policy)


def propose_ml_review_policy(*, division: str, policy: dict, actor: str,
                             reason: str | None = None, config=None) -> Event:
    """Submit a division's draft ML review policy for MRC sign-off."""
    return _POLICY.propose(division=division, policy=policy, actor=actor,
                           reason=reason, config=config)


def approve_ml_review_policy(*, division: str, actor: str,
                             meeting_id: str | None = None,
                             reason: str | None = None, config=None) -> Event:
    """Ratify the pending draft: it becomes the policy reviews are judged against."""
    return _POLICY.approve(division=division, actor=actor, meeting_id=meeting_id,
                           reason=reason, config=config)


def reject_ml_review_policy(*, division: str, actor: str,
                            meeting_id: str | None = None,
                            reason: str | None = None, config=None) -> Event:
    """Decline or withdraw the pending draft. The live policy is unchanged."""
    return _POLICY.reject(division=division, actor=actor, meeting_id=meeting_id,
                          reason=reason, config=config)
