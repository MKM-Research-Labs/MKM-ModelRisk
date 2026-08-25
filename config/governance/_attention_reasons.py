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
"""The obligations the dashboard can report, and what each one implies (rule R1).

Split from ``_attention`` — which holds the four states, the precedence and the
horizon — because the table itself is the part that grows: every new obligation the
platform learns to notice adds an entry here, and it had pushed that module over the
300-line gate. The states it refers to are stable; this is the list that is not.

Each entry is the whole of what the dashboard knows about a reason. Nothing about
wording, severity or grouping is decided in the module that counts.
"""
from __future__ import annotations

from config.governance._attention import (
    REASON_BELOW_STANDARD,
    REASON_COMMITTEE_ACTION_OPEN,
    REASON_EVIDENCE_MISSING,
    REASON_FINDING_OPEN,
    REASON_FINDING_PAST_SLA,
    REASON_POLICY_UNRATIFIED,
    REASON_REMEDIATION_DUE_SOON,
    REASON_REMEDIATION_OVERDUE,
    REASON_REVIEWER_NOT_INDEPENDENT,
    REASON_REVIEW_DUE_SOON,
    REASON_REVIEW_OVERDUE,
    REASON_SIGNOFF_MISSING,
    STATE_ACT,
    STATE_CLEAR,
    STATE_ESCALATE,
    STATE_MONITOR,
)

# ``state``       which of the four this reason implies.
# ``label``       how the row reads. Adopter-configurable.
# ``action``      the instruction, for reasons the audit does not already word.
#                 Absent where the finding carries its own (see the docstring).
# ``grouped``     whether many of these collapse into one queue row.
# ``group_by``    what they collapse ON. Absent means one row for the whole reason;
#                 "owner" means one row per person, which keeps the name that makes
#                 the row chaseable while still collapsing twenty of them.
# ``count_label`` how a COUNT of these reads, as (singular, plural). Used for the
#                 collapsed row and for the verdict sentence, so the headline an
#                 executive reads is assembled from configuration rather than
#                 written into the module that counts.
ATTENTION_REASONS = {
    REASON_REVIEWER_NOT_INDEPENDENT: {
        "state": STATE_ESCALATE,
        "label": "Reviewer is the record's own owner",
        "count_label": ("{count} record is reviewed by its own owner",
                        "{count} records are reviewed by their own owner"),
        "grouped": False,
    },
    REASON_EVIDENCE_MISSING: {
        "state": STATE_ESCALATE,
        "label": "Evidence cited but not held",
        "count_label": ("{count} record cites evidence that cannot be produced",
                        "{count} records cite evidence that cannot be produced"),
        "grouped": False,
    },
    REASON_SIGNOFF_MISSING: {
        "state": STATE_ESCALATE,
        "label": "No committee sign-off",
        "count_label": ("{count} record carries no committee sign-off",
                        "{count} records carry no committee sign-off"),
        "grouped": True,
    },
    REASON_POLICY_UNRATIFIED: {
        "state": STATE_ESCALATE,
        "label": "Risk policy has never been ratified",
        "count_label": ("{count} division runs on an unratified risk policy",
                        "{count} divisions run on an unratified risk policy"),
        "action": "Table the division's risk policy for ratification at its "
                  "next committee.",
        "grouped": False,
    },
    REASON_REVIEW_OVERDUE: {
        "state": STATE_ACT,
        "label": "Review overdue",
        "count_label": ("{count} review is overdue", "{count} reviews are overdue"),
        "action": "Complete the scheduled review and record its outcome.",
        "grouped": False,
    },
    REASON_BELOW_STANDARD: {
        "state": STATE_ACT,
        "label": "Below the acceptable completeness standard",
        "count_label": ("{count} record is below the acceptable standard",
                        "{count} records are below the acceptable standard"),
        "action": "Close the outstanding gaps until the record reaches its "
                  "division's threshold.",
        "grouped": True,
    },
    REASON_REMEDIATION_OVERDUE: {
        "state": STATE_ACT,
        "label": "Remediation overdue",
        "count_label": ("{count} remediation step is past its date",
                        "{count} remediation steps are past their date"),
        "action": "Complete the remediation step, or agree a new date with the "
                  "committee that set it.",
        # Grouped BY OWNER rather than not at all. Each is a specific commitment by
        # a named person, so the name is the one thing that must survive collapsing
        # -- but a real estate produces twenty of these, and twenty near-identical
        # rows bury the findings that are singular. One row per person keeps the
        # chase intact and the page readable: the response to twenty overdue steps
        # is a conversation with the three people who owe them, not a list.
        "grouped": True,
        "group_by": "owner",
    },
    REASON_REVIEW_DUE_SOON: {
        "state": STATE_MONITOR,
        "label": "Review due",
        "count_label": ("{count} review falls due within the horizon",
                        "{count} reviews fall due within the horizon"),
        "action": "Schedule the review before its date.",
        "grouped": False,
    },
    REASON_REMEDIATION_DUE_SOON: {
        "state": STATE_MONITOR,
        "label": "Remediation due",
        "count_label": ("{count} remediation step falls due within the horizon",
                        "{count} remediation steps fall due within the horizon"),
        "action": "Complete the remediation step before its date.",
        "grouped": True,
    },
    # An MRC action is agreed WITHOUT a target date -- progress is recorded as
    # dated updates instead (config.governance._mrc, "actions"). So it can be
    # reported as outstanding but never as late: calling it overdue would put a
    # deadline in front of an executive that no committee ever set.
    REASON_COMMITTEE_ACTION_OPEN: {
        "state": STATE_MONITOR,
        "label": "Committee action still open",
        "count_label": ("{count} committee action is still open",
                        "{count} committee actions are still open"),
        "action": "Report progress to the committee, or request closure with the "
                  "evidence that settles it.",
        "grouped": True,
    },
    # A finding that has outlived the remediation deadline its own band sets. It
    # needs the finding history to exist: the audit is computed fresh each run and
    # cannot say how long a gap has been open, and an age nobody measured is not an
    # age. Without the history every finding stays with its owner, which is the
    # honest reading rather than a flattering one.
    REASON_FINDING_PAST_SLA: {
        "state": STATE_ACT,
        "label": "Findings past their remediation deadline",
        "count_label": ("{count} record has findings past their remediation deadline",
                        "{count} records have findings past their remediation deadline"),
        "action": "Close the outstanding findings, or take the delay to the "
                  "committee that set the deadline.",
        "grouped": True,
    },
    REASON_FINDING_OPEN: {
        "state": STATE_CLEAR,
        "label": "Open findings, with their owner",
        "count_label": ("{count} record carries open findings and meets the standard",
                        "{count} records carry open findings and meet the standard"),
        "grouped": True,
    },
}

__all__ = ["ATTENTION_REASONS"]
