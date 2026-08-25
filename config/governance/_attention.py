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
"""What the dashboard treats as needing a response (coding rule R1).

The completeness audit asks whether each record is complete. This table answers
the question one level up: of everything the audit and the committee registers
already know, what does a chief risk officer have to do something about?

Three things live here and nowhere else.

**The four states.** A reader at that level has four available responses, so
every item resolves to one of four. The machine values are frozen — an ERM
integration is written against them and has to survive a rename — while the
labels beside them are an adopter's to re-set like every other vocabulary in the
platform.

**The reasons.** Each names one obligation, the state it implies, and whether it
is aggregated into a single queue row. Only the reasons the audit does not
already speak for carry an ``action`` here: where a reason is derived from an
audit gap, the instruction travels on the gap (``REMEDIATION_ACTIONS`` and the
rule templates), so the dashboard cannot word a finding differently from the
report a committee signed.

**The precedence.** A record contributes at most ONE item — the worst obligation
standing against it. Without that, a badly-kept record appears three times and
the executive's count measures how many ways one record is behind rather than how
many records are. Committee actions and un-ratified division policies are items
in their own right, because they belong to a meeting and to a division rather
than to a record.
"""
from __future__ import annotations

from config.governance._mrc import REVIEW_DUE_SOON_DAYS

# ---------------------------------------------------------------------------
# The four states.
# ---------------------------------------------------------------------------
STATE_ESCALATE = "escalate"
STATE_ACT = "act"
STATE_MONITOR = "monitor"
STATE_CLEAR = "clear"

# Ordered worst first. The dashboard, the drill-down and the API all tally in
# this order, so a reader meets the same sequence wherever they look.
ATTENTION_STATES = (STATE_ESCALATE, STATE_ACT, STATE_MONITOR, STATE_CLEAR)

# The states that reach the executive. Everything else is with an owner, and the
# page says so rather than counting it against the reader.
RESPONSE_STATES = (STATE_ESCALATE, STATE_ACT)

# What each state is CALLED. Renaming one here renames it on the dashboard and in
# the API's ``*_label`` fields; the machine values above do not move.
ATTENTION_STATE_LABELS = {
    STATE_ESCALATE: "Escalate",
    STATE_ACT: "Act",
    STATE_MONITOR: "Monitor",
    STATE_CLEAR: "Clear",
}

# What each state's CARD is headed on the dashboard. Plain English for a reader who
# should not have to learn a vocabulary to use the page, held here rather than in the
# JavaScript so it is an adopter's to change like every other word on the screen.
ATTENTION_STATE_CARD = {
    STATE_ESCALATE: "Breaches",
    STATE_ACT: "Needs you",
    STATE_MONITOR: "Worth noting",
    STATE_CLEAR: "With owners",
}

# How each state reads as an instruction, for the line beneath the number.
ATTENTION_STATE_RESPONSE = {
    STATE_ESCALATE: "Yours. Take it to the committee.",
    STATE_ACT: "Chase the named owner.",
    STATE_MONITOR: "Nothing today. Note it.",
    STATE_CLEAR: "Nothing.",
}

# ---------------------------------------------------------------------------
# The horizon.
# ---------------------------------------------------------------------------
# How far ahead "coming due" looks: the SAME horizon the model register already
# calls Due Soon. Deliberately an alias rather than a second constant — two
# horizons would let the Models tab call a review Due Soon on a day the dashboard
# still counted it clear, with nothing on either screen to say why. An adopter on
# a quarterly committee cycle raises REVIEW_DUE_SOON_DAYS and both move together.
COMING_DUE_DAYS = REVIEW_DUE_SOON_DAYS

# The most items the queue will carry. Reached only by an estate in a state no
# dashboard can help with; when it bites, the count is still reported in full and
# the truncation is declared rather than left to look like completeness.
ATTENTION_QUEUE_CAP = 200

# ---------------------------------------------------------------------------
# The reasons.
# ---------------------------------------------------------------------------
REASON_REVIEWER_NOT_INDEPENDENT = "reviewer_not_independent"
REASON_EVIDENCE_MISSING = "evidence_missing"
REASON_SIGNOFF_MISSING = "signoff_missing"
REASON_POLICY_UNRATIFIED = "risk_policy_unratified"
REASON_REVIEW_OVERDUE = "review_overdue"
REASON_BELOW_STANDARD = "record_below_standard"
REASON_REMEDIATION_OVERDUE = "remediation_overdue"
REASON_REVIEW_DUE_SOON = "review_due_soon"
REASON_REMEDIATION_DUE_SOON = "remediation_due_soon"
REASON_COMMITTEE_ACTION_OPEN = "committee_action_open"
REASON_FINDING_PAST_SLA = "finding_past_sla"
REASON_FINDING_OPEN = "finding_open"

# The one obligation a record reports, worst first. A record matching none of
# these is clear and produces no item at all.
ATTENTION_PRECEDENCE = (
    REASON_REVIEWER_NOT_INDEPENDENT,
    REASON_EVIDENCE_MISSING,
    REASON_SIGNOFF_MISSING,
    REASON_REVIEW_OVERDUE,
    REASON_BELOW_STANDARD,
    REASON_FINDING_PAST_SLA,
    REASON_REVIEW_DUE_SOON,
    REASON_FINDING_OPEN,
)

# ---------------------------------------------------------------------------
# Where each record-level reason is read FROM.
# ---------------------------------------------------------------------------
# The dashboard derives no finding of its own: three of the record-level reasons
# are an audit gap under another name, and this is the mapping. Naming the gap
# here rather than in the module keeps the coupling visible — if the audit renames
# a gap, the failure is a missing key in configuration, not a silently empty card.
REASON_FROM_GAP_KIND = {
    "document_broken": REASON_EVIDENCE_MISSING,
}
REASON_FROM_GAP_KEY = {
    "reviewer_independence": REASON_REVIEWER_NOT_INDEPENDENT,
    "mrc_signoff_date": REASON_SIGNOFF_MISSING,
}

# Review currency is not re-derived either: ``compute_review_status`` already
# classifies a next-review date for the Models tab, and this maps its verdict onto
# a reason. A record the register calls Overdue and the dashboard called something
# else would be the same failure the audit coupling above avoids.
REASON_FROM_REVIEW_STATUS = {
    "Overdue": REASON_REVIEW_OVERDUE,
    "Due Soon": REASON_REVIEW_DUE_SOON,
}

__all__ = [
    "ATTENTION_PRECEDENCE", "ATTENTION_QUEUE_CAP", "ATTENTION_STATES", "ATTENTION_STATE_CARD", "ATTENTION_STATE_LABELS",
    "ATTENTION_STATE_RESPONSE",
    "COMING_DUE_DAYS", "REASON_BELOW_STANDARD", "REASON_COMMITTEE_ACTION_OPEN",
    "REASON_EVIDENCE_MISSING", "REASON_FINDING_OPEN", "REASON_FINDING_PAST_SLA",
    "REASON_FROM_GAP_KEY",
    "REASON_FROM_GAP_KIND", "REASON_FROM_REVIEW_STATUS", "REASON_POLICY_UNRATIFIED",
    "REASON_REMEDIATION_DUE_SOON", "REASON_REMEDIATION_OVERDUE",
    "REASON_REVIEWER_NOT_INDEPENDENT", "REASON_REVIEW_DUE_SOON",
    "REASON_REVIEW_OVERDUE", "REASON_SIGNOFF_MISSING", "RESPONSE_STATES",
    "STATE_ACT", "STATE_CLEAR", "STATE_ESCALATE", "STATE_MONITOR",
]
