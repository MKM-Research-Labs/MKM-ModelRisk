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
"""Who may author a change (coding rule R1). Phase P1 of ``docs/permissions_design.md``.

The identity header is taken at face value — whatever string arrives becomes the event's
actor — so an unregistered identity could author on the governance record. On 2026-08-06
``alice@corp``, the header hardcoded in the web tests, authored 24 real events from an
ad-hoc script. This is the rule that refuses that: a change must be authored by somebody
the institution has registered under Admin -> People.

It is deliberately NOT a role model. Roles, segregation of duties and machine-actor
scoping are later phases; this only answers "is the author a real, registered person".
"""
from __future__ import annotations

import os

# When the known-actor rule applies:
#   "protected" — only against a protected database (the real estate). Test and scratch
#                 databases stay open, so the suite and throwaway environments are
#                 unaffected. This is the default.
#   "always"    — every database. What a hardened deployment should set.
#   "never"     — disabled. A break-glass switch for an adopter mid-migration; it leaves
#                 the governance record open to any identity, so it should be temporary.
ENFORCE_KNOWN_ACTORS = os.environ.get("ENFORCE_KNOWN_ACTORS", "protected")

# Actors that are legitimate without being people:
#   the platform's own actor for first-run seeding, and machine producers, whose ids are
#   prefixed so the audit trail never mistakes an ingested payload for a person's work.
# Scoping machine actors to append-only is phase P6, not this rule.
MACHINE_ACTOR_PREFIX = "ingest:"

# Segregation of duties: a model's peer reviewer may not be its own owner. A review by
# the person who owns the model is a review, but not an independent one, and the record
# cannot tell the two apart by itself -- both fields are populated, so the completeness
# score reads the model as governed. It is the first thing an external assessor checks
# (ISO 31000 5.4.3, COSO ERM principle 2).
#
# Set "never" for an adopter mid-migration whose estate cannot yet satisfy it; existing
# breaches are reported by the completeness audit either way, and enforcement here only
# refuses the write that would create or keep one, so no record is ever locked shut.
ENFORCE_REVIEWER_INDEPENDENCE = os.environ.get("ENFORCE_REVIEWER_INDEPENDENCE", "always")

# An institution with no People registered yet cannot be locked out of registering the
# first one — a fresh install has an empty list and a protected database name. While the
# list is empty the rule stands down; the first person added closes it.
ALLOW_WHEN_NO_PEOPLE_REGISTERED = True

# ---------------------------------------------------------------------------
# Phase P2: what a person can BE. Held on their People record; a person may hold several
# (an owner who also sits on a committee is ordinary). The explanations are shown beside
# the choice, so an administrator assigning a role can see what they are granting —
# the same treatment the risk policy gives its bands.
#
# This is the vocabulary an adopting institution re-sets to its own framework. Changing a
# role's NAME here without changing it on the People records that hold it un-assigns it,
# exactly as renaming a risk band would; add a new role and migrate rather than rename in
# place on a live estate.
# ---------------------------------------------------------------------------
ROLES = {
    "owner": "Owns models or products: sets their classification and rationale, and asks "
             "the committee to sign them off.",
    "validator": "Validates models independently of the people who built them, and "
                 "answers the validation questions.",
    "committee": "Sits on an MRC: votes on sign-off, ratification and retirement.",
    "chair": "Chairs an MRC: tables papers, closes meetings and records decisions.",
    "administrator": "Maintains the admin reference lists and drafts the risk policy for "
                     "the committee to ratify.",
    "reader": "Reads the governance record; authors nothing.",
}
