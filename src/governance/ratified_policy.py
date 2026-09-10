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
"""A policy the MRC ratifies: Proposed → Approved / Rejected.

Two things in this codebase are settings an institution writes down and a committee
then stands behind — the risk policy (what a rating *means* in a division) and the ML
review policy (what a review must *contain*). Both are per division, because one
division's standard cannot describe another's work, and both are worthless if an
owner can change them the week before an inspection. So both are the same lifecycle:

    <Name>Proposed   → a draft submitted for sign-off (carries the whole policy)
    <Name>Approved   → the division's MRC ratified it; it becomes the LIVE policy
    <Name>Rejected   → the draft is withdrawn or declined; the live policy stands

``live`` is what records actually use: the most recently approved policy, or the
firm-wide default for a division that has never ratified its own. ``draft`` is read
separately by the admin editor and drives nothing until it is approved.

This module is the lifecycle once. ``risk_policy`` and ``ml_review_policy`` differ in
what a policy *is* and what makes one valid, which arrive as ``default`` and
``validate``; they do not differ in how a committee ratifies one, and writing that out
twice is how a rule ends up fixed in one copy and not the other.

**The stream is keyed on a SCOPE, which is usually but not always a division.** It was
spelled ``division`` throughout until 2026-09-09, when the lifecycle stage catalogue
arrived: one document for the whole institution, stored under a single fixed id. That
is a scope of one, and the lifecycle is otherwise identical -- so the parameter is named
for what it is, and ``scope_noun=None`` marks a singleton whose refusals must not name a
scope its reader cannot see ("global has no proposed catalogue" helps nobody).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from src.database import Event, append_event, read_stream
from src.governance.errors import DomainError

# Lifecycle states surfaced to the UI.
STATE_SEED = "seed"          # nothing ever ratified — running on the default
STATE_APPROVED = "approved"  # a division-specific policy is live, no draft outstanding
STATE_DRAFT = "draft"        # a proposed policy is awaiting the division's MRC sign-off


def recorded_date(recorded_at) -> str | None:
    """The date (YYYY-MM-DD) an event was recorded.

    Kept as a date, not a timestamp, because what it answers is "was this record
    signed off under the current policy or an older one?" — a question about days.
    """
    if recorded_at is None:
        return None
    if hasattr(recorded_at, "date"):
        return recorded_at.date().isoformat()
    return str(recorded_at)[:10]


@dataclass(frozen=True)
class RatifiedPolicy:
    """The lifecycle for one kind of MRC-ratified policy.

    ``noun`` appears in the refusals, so a caller reads "PhysicalRisk has no proposed
    ML review policy awaiting sign-off" rather than a generic message that leaves them
    guessing which policy the committee has not seen.
    """

    aggregate_type: str
    noun: str
    default: Callable[[], Any]
    validate: Callable[[Any], None] | None = None
    # An optional extra event some policies carry (the risk policy's uploaded
    # document). Folded into ``load`` when present so it survives a rebuild.
    document_event: str | None = None
    # What the stream is keyed on, as a refusal should name it. Every policy that is
    # ratified per org unit is keyed on a division; ``None`` marks a SINGLETON -- one
    # document for the whole institution under one fixed id -- and switches the wording
    # to sentences that do not mention a scope at all.
    scope_noun: str | None = "division"

    @property
    def singleton(self) -> bool:
        """One document for the institution, rather than one per scope."""
        return self.scope_noun is None

    @property
    def proposed_event(self) -> str:
        return f"{self.aggregate_type}Proposed"

    @property
    def approved_event(self) -> str:
        return f"{self.aggregate_type}Approved"

    @property
    def rejected_event(self) -> str:
        return f"{self.aggregate_type}Rejected"

    def load(self, scope: str, config=None) -> dict:
        """Fold one scope's stream into ``{live, draft, document, state, approved,
        approved_at, version}``."""
        live = self.default()
        draft = document = approved_at = None
        approved = False
        version = 0
        for event in read_stream(aggregate_type=self.aggregate_type,
                                 aggregate_id=scope, config=config):
            if event.event_type == self.proposed_event:
                draft = event.payload["policy"]
            elif event.event_type == self.approved_event:
                live = event.payload["policy"]
                draft = None
                approved = True
                # When the live policy was ratified — a record signed off before this
                # date was assessed under an older one.
                approved_at = recorded_date(event.recorded_at)
            elif event.event_type == self.rejected_event:
                draft = None
            elif self.document_event and event.event_type == self.document_event:
                document = {"filename": event.payload["filename"],
                            "original_name": event.payload["original_name"]}
            version = event.stream_seq
        state = (STATE_DRAFT if draft is not None
                 else STATE_APPROVED if approved else STATE_SEED)
        return {"live": live, "draft": draft, "document": document, "state": state,
                "approved": approved, "approved_at": approved_at, "version": version}

    def live(self, scope: str, config=None):
        """The policy this scope's records actually use."""
        return self.load(scope, config)["live"]

    def draft(self, scope: str, config=None):
        """The proposal awaiting MRC sign-off, or None."""
        return self.load(scope, config)["draft"]

    def propose(self, *, scope: str, policy, actor: str,
                reason: str | None = None, config=None) -> Event:
        """Submit a draft for MRC sign-off.

        Validated now, so a broken policy never reaches the committee; it stays a
        draft either way until somebody approves it.
        """
        if not self.singleton and not str(scope).strip():
            raise DomainError(f"a {self.noun} must belong to a {self.scope_noun}")
        if self.validate:
            self.validate(policy)
        return self._append(scope, self.proposed_event, {"policy": policy},
                            actor, reason, config)

    def approve(self, *, scope: str, actor: str, meeting_id: str | None = None,
                reason: str | None = None, config=None) -> Event:
        """Ratify the pending draft: it becomes the live policy.

        Records the meeting it was approved at, because "the committee agreed this"
        is only evidence if you can say which sitting.
        """
        state = self._require_draft(scope, "awaiting sign-off", config)
        return self._append(scope, self.approved_event,
                            {"policy": state["draft"], "meeting_id": meeting_id},
                            actor, reason, config, state=state)

    def reject(self, *, scope: str, actor: str, meeting_id: str | None = None,
               reason: str | None = None, config=None) -> Event:
        """Decline or withdraw the pending draft. The live policy is unchanged."""
        state = self._require_draft(scope, "to reject", config)
        return self._append(scope, self.rejected_event, {"meeting_id": meeting_id},
                            actor, reason, config, state=state)

    def _require_draft(self, scope: str, what: str, config) -> dict:
        state = self.load(scope, config)
        if state["draft"] is None:
            # A singleton has no scope worth naming: "there is no proposed lifecycle
            # stage catalogue awaiting sign-off" says the whole of it, where naming the
            # fixed id it is stored under would only puzzle the reader.
            if self.singleton:
                raise DomainError(f"there is no proposed {self.noun} {what}")
            raise DomainError(f"{scope} has no proposed {self.noun} {what}")
        return state

    def _append(self, scope: str, event_type: str, payload: dict, actor: str,
                reason: str | None, config, state: dict | None = None) -> Event:
        state = state if state is not None else self.load(scope, config)
        return append_event(
            aggregate_type=self.aggregate_type, aggregate_id=scope,
            event_type=event_type, payload=payload, actor=actor, reason=reason,
            expected_version=state["version"], config=config,
        )
