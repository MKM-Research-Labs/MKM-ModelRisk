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
"""The running order every meeting is seeded with (coding rule R1).

Its own module because it is a seed, not a schema: an adopter edits the list under
Admin → Agenda and each meeting keeps the copy it was given. What stays fixed is a
standing item's ``kind``, which decides the bespoke panel a meeting draws for it.
"""
from __future__ import annotations

# The standing agenda seeded onto every new MRC meeting, in running order (AOB
# always last). Each item's ``kind`` drives the bespoke per-item UI renderer and
# marks it as a template item, so generic agenda replay (the demo seeder) skips
# these to avoid duplicating what the seeding helper already adds.
STANDING_AGENDA = (
    {"kind": "rollcall", "title": "Rollcall and Confirmation of Quorum",
     "description": "Confirm attendance in the participants panel; the meeting "
                    "may proceed only once quorate."},
    {"kind": "minutes_signoff", "title": "Sign-off of the previous MRM minutes",
     "description": "Proposed by the chair."},
    {"kind": "review_signoff", "title": "Review model sign-off",
     "description": "Risk-rating sign-offs are reviewed in the Models tab (Approvals)."},
    {"kind": "review_analysis", "title": "Review model analysis",
     "description": "Model analyses are reviewed in the Models tab (Analysis) — "
                    "confirmation to proceed and any actions."},
    {"kind": "completeness_audit", "title": "Governance completeness audit",
     "description": "Run and review the completeness audit for the models and "
                    "products in scope for this committee; record the committee's "
                    "notes on the outcome."},
    # Who sits on this committee, and what they are allowed to be. A person's roles
    # decide who may own, validate and approve, so granting them is the committee's
    # decision rather than an administrator's — the same reasoning that sends the risk
    # policy here rather than letting Admin set it directly.
    {"kind": "membership", "title": "Committee membership and roles",
     "description": "Ratify proposed changes to who sits on this committee and the "
                    "roles they hold. Proposed in Admin -> People; a role takes effect "
                    "only once ratified here."},
    {"kind": "aob", "title": "Any Other Business (AOB)", "description": ""},
)
STANDING_AGENDA_KINDS = frozenset(item["kind"] for item in STANDING_AGENDA)
# The same roles in the order a meeting runs them, for the Admin picker: a set has
# no order, and a dropdown that shuffled between page loads would be its own bug.
STANDING_AGENDA_ROLES = tuple(dict.fromkeys(item["kind"] for item in STANDING_AGENDA))
