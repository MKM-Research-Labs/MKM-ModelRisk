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
signed it off.

The lifecycle itself -- Proposed → Approved / Rejected, and the fold that turns a
stream into ``{live, draft, state, ...}`` -- lives in ``ratified_policy``, shared with
the ML review policy. What is here is what makes a RISK policy specific: its default,
and the validation in ``commands``.

``get_risk_policy(division)`` returns the LIVE policy a division's models actually use --
the most recently approved one, or the firm-wide seed ``default_policy()`` for a division
that has never ratified its own. The pending draft (if any) is read separately by the
admin editor; it does not drive ratings until approved.
"""
from __future__ import annotations

from src.governance.ratified_policy import (STATE_APPROVED, STATE_DRAFT, STATE_SEED,
                                            RatifiedPolicy, recorded_date)
from src.governance.risk_policy._defaults import default_policy

AGGREGATE_TYPE = "RiskPolicy"
EVENT_POLICY_DOCUMENT = "RiskPolicyDocumentUploaded"

# Validation is applied by ``commands.propose_policy``, which owns the rules about what
# a risk policy may contain; the lifecycle only needs to know how to store one.
POLICY = RatifiedPolicy(aggregate_type=AGGREGATE_TYPE, noun="risk policy",
                        default=default_policy, document_event=EVENT_POLICY_DOCUMENT)

EVENT_POLICY_PROPOSED = POLICY.proposed_event
EVENT_POLICY_APPROVED = POLICY.approved_event
EVENT_POLICY_REJECTED = POLICY.rejected_event

# Re-exported: these were this module's names before the lifecycle moved out, and
# callers (the API, the admin editor) still read them from here.
__all__ = ["AGGREGATE_TYPE", "EVENT_POLICY_PROPOSED", "EVENT_POLICY_APPROVED",
           "EVENT_POLICY_REJECTED", "EVENT_POLICY_DOCUMENT", "POLICY",
           "STATE_SEED", "STATE_APPROVED", "STATE_DRAFT",
           "load", "get_risk_policy", "get_policy_draft"]


def load(division: str, config=None) -> dict:
    """Fold a division's stream into its current state.

    Returns ``{live, draft, state, approved, version}`` where ``live`` is the policy
    models use, ``draft`` is a proposal awaiting sign-off (or None), and ``approved`` is
    whether any division-specific policy has ever been ratified.
    """
    return POLICY.load(division, config)


def get_risk_policy(division: str, config=None) -> dict:
    """The LIVE risk policy a division's models use: its most recently MRC-approved
    policy, or the firm-wide seed default until the division ratifies its own."""
    return POLICY.live(division, config)


def get_policy_draft(division: str, config=None) -> dict | None:
    """The division's proposed policy awaiting MRC sign-off, or None."""
    return POLICY.draft(division, config)


# Kept for callers that imported it from here before it moved.
_recorded_date = recorded_date
