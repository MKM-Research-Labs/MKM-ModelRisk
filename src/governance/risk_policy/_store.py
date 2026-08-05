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
"""Risk policy store: one event-sourced policy PER DIVISION, gated by MRC sign-off.

Each division defines its own risk vocabulary (Moody's Ratings need not see risk the
way Moody's Analytics does), and a change only goes live once that division's MRC has
signed it off. So a division's stream is a lifecycle:

    RiskPolicyProposed   → a draft submitted for sign-off (carries the full policy)
    RiskPolicyApproved   → the division's MRC ratified it; it becomes the LIVE policy
    RiskPolicyRejected   → the draft is withdrawn/declined; the live policy is unchanged

``get_risk_policy(division)`` returns the LIVE policy a division's models actually use —
the most recently approved one, or the firm-wide seed ``default_policy()`` for a division
that has never ratified its own. The pending draft (if any) is read separately by the
admin editor; it does not drive ratings until approved.
"""
from __future__ import annotations

from src.database import read_stream
from src.governance.risk_policy._defaults import default_policy

AGGREGATE_TYPE = "RiskPolicy"
EVENT_POLICY_PROPOSED = "RiskPolicyProposed"
EVENT_POLICY_APPROVED = "RiskPolicyApproved"
EVENT_POLICY_REJECTED = "RiskPolicyRejected"

# Lifecycle states surfaced to the UI.
STATE_SEED = "seed"          # no policy ever ratified — running on the firm-wide default
STATE_APPROVED = "approved"  # a division-specific policy is live, no draft outstanding
STATE_DRAFT = "draft"        # a proposed policy is awaiting the division's MRC sign-off


def load(division: str, config=None) -> dict:
    """Fold a division's stream into its current state.

    Returns ``{live, draft, state, approved, version}`` where ``live`` is the policy
    models use, ``draft`` is a proposal awaiting sign-off (or None), and ``approved`` is
    whether any division-specific policy has ever been ratified.
    """
    live = default_policy()
    draft = None
    approved = False
    version = 0
    for event in read_stream(
        aggregate_type=AGGREGATE_TYPE, aggregate_id=division, config=config
    ):
        if event.event_type == EVENT_POLICY_PROPOSED:
            draft = event.payload["policy"]
        elif event.event_type == EVENT_POLICY_APPROVED:
            live = event.payload["policy"]
            draft = None
            approved = True
        elif event.event_type == EVENT_POLICY_REJECTED:
            draft = None
        version = event.stream_seq
    state = STATE_DRAFT if draft is not None else (STATE_APPROVED if approved else STATE_SEED)
    return {"live": live, "draft": draft, "state": state,
            "approved": approved, "version": version}


def get_risk_policy(division: str, config=None) -> dict:
    """The LIVE risk policy a division's models use: its most recently MRC-approved
    policy, or the firm-wide seed default until the division ratifies its own."""
    return load(division, config)["live"]


def get_policy_draft(division: str, config=None) -> dict | None:
    """The division's proposed policy awaiting MRC sign-off, or None."""
    return load(division, config)["draft"]
