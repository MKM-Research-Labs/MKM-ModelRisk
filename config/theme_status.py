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
"""Which token each status is drawn in — the mapping, not the colours.

Split from ``theme.py`` at the seam that module already had. Everything there is a
token: a name and the colour it stands for. Everything here is a mapping from a value
the platform stores — a RAG rating, a meeting status, a change tier — onto one of those
token names, and it contains no colour at all. A reader asking "what green is our
green" and one asking "what is drawn green" are asking different questions.

Re-exported from ``config.theme`` so every existing import goes on working.
"""
from __future__ import annotations

# --- What colour a status is drawn in --------------------------------------------
# Six maps in helpers.js held 27 entries between them and used five colours: they were
# six spellings of one vocabulary, and one of them had already been half-converted to
# var(--red) by hand. Here they are one table, and they name a TOKEN rather than a
# colour — so an adopter recolours by editing the token, and re-maps by editing this.
#
# Keys are the stored value, as a string: these arrive over JSON, where an object key
# is always a string, and mission criticality is keyed by its band score.
STATUS_COLOUR_TOKENS = {
    "rag": {"Green": "green", "Amber": "amber", "Red": "red"},
    # Scores 4 and 5 have no seeded band (the seed defines three); they are carried
    # because a division may define more, and a record may still hold an old score.
    "mission_criticality": {"1": "red", "2": "amber", "3": "accent", "4": "green",
                            "5": "grey"},
    "meeting_status": {"Scheduled": "accent", "In Progress": "amber", "Held": "green",
                       "Cancelled": "grey"},
    "validation_question": {"Addressed": "green", "Partially Addressed": "amber",
                            "Not Addressed": "red", "Not Applicable": "grey"},
    # Everything short of a live sign-off is amber: work outstanding, not a failure.
    "mrc_state": {"Pending": "amber", "Rejected": "red", "Revoked": "red",
                  "Re-classify": "amber", "Rating moved": "amber",
                  "Not placed": "grey", "Approved": "green"},
    "lifecycle": {"New": "accent", "Being Enhanced": "amber",
                  "No New Development": "grey", "Marked for Removal": "red"},
    "product_status": {"Active": "green", "Proposed": "info", "Suspended": "amber",
                       "Retired": "grey"},
    # A reviewer's challenge: outstanding, or answered by the owner.
    "review_thread": {"open": "violet", "answered": "blue-grey"},
    # The dashboard's four response states. Escalate and Act are the two that
    # reach the executive, so they take the two alarm colours; Monitor is drawn in
    # the accent rather than a third warning shade, because "note it" is not a
    # lesser emergency -- it is a different kind of thing.
    "attention": {"escalate": "red", "act": "amber", "monitor": "accent",
                  "clear": "green"},
    # The four change tiers. Ascending severity, and drawn so a reader can rank them
    # at a glance without reading the word: Material takes the alarm colour because it
    # invalidates the approval the record holds. Measurement is amber rather than a
    # second red -- the record still does what it did, but the evidence for it was
    # produced by a different instrument. Administrative is grey deliberately: a
    # register where every row looks urgent is one nobody scans.
    "change_class": {"Administrative": "grey", "Bounded": "accent",
                     "Measurement": "amber", "Material": "red"},
    # Lineage node kinds. The three the institution governs take the platform's own
    # colours; the two it does not — a foundation model somebody else versions, an MCP
    # server outside the firm — take the warning shades, because what a chain diagram
    # is FOR is showing where the firm's perimeter ends.
    "lineage_node": {"MODEL": "accent", "ML_APPLICATION": "blue-grey",
                     "AI_SYSTEM": "violet", "FOUNDATION_MODEL": "amber",
                     "MCP_SERVER": "red"},
}

# What an unrecognised value is drawn in, per domain. A domain absent from here has no
# default on purpose: an unknown rating or an unrated tier must render as a dash, not
# as a grey badge asserting a classification nobody made.
STATUS_COLOUR_DEFAULTS = {
    # An unclassified change has no tier yet, and grey says so without asserting one.
    "change_class": "grey",
    # A node kind nothing recognises is drawn as one the platform does not govern,
    # which is the safer of the two readings.
    "lineage_node": "grey",
    "validation_question": "grey",
    "mrc_state": "grey",
    "lifecycle": "grey",
    "product_status": "grey",
}
