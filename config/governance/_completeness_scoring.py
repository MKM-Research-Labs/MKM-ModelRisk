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
"""How a completeness gap is escalated, banded and actioned (coding rule R1).

Split from ``_completeness``, which says what each missing thing is *worth*.
This module says what happens to that weight once the record it belongs to is
taken into account -- the escalation factors, the bands they fall into, and the
instruction and target date attached to each. The two get challenged by
different readers: an owner argues with the criticality of a field, a committee
argues with the thresholds.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Escalation factors. Each is centred on 1.0 -- a factor that does not apply
# leaves the severity where the criticality put it.
# ---------------------------------------------------------------------------

# Tier is the institution's own statement of how much the model matters, so it is
# the primary escalation. Tier 3 is damped rather than zeroed: "not important"
# is not "unaudited".
TIER_WEIGHTS = {1: 1.00, 2: 0.80, 3: 0.60}
UNTIERED_WEIGHT = 0.90          # an untiered model is treated as nearly Tier 1:
                                # the absent tier is itself the reason to look.

RAG_MULTIPLIERS = {"Red": 1.25, "Amber": 1.10, "Green": 1.00}
# An unrated model escalates above Green. A missing rating is not evidence of a
# healthy one, and treating it as Green would let the least-governed models sink
# to the bottom of the remediation list.
UNRATED_MULTIPLIER = 1.15

# Operational failure events in the rolling window (EVENTS_WINDOW_DAYS). A model
# that has actually failed in production carries more weight than one that has
# not, and the effect is capped so a single bad year cannot dominate the ranking.
EVENT_PRESSURE_PER_EVENT = 0.05
EVENT_PRESSURE_CAP = 1.25

# Review staleness, applied against next_review_date. A record that was complete
# at its last review and has since gone unreviewed is a weaker assurance than the
# same record reviewed last month.
STALENESS_STEPS = (
    # (days overdue at or beyond, multiplier)
    (365, 1.20),
    (180, 1.12),
    (90, 1.07),
    (0, 1.03),
)
STALENESS_NONE = 1.00

# ---------------------------------------------------------------------------
# Bands and remediation.
# ---------------------------------------------------------------------------
# (label, score at or above). Ordered worst first; the first match wins.
#
# Calibrated against the escalation range rather than the raw criticality scale,
# which spans 0.30-1.00 while escalation spans 0.60 (Tier 3, Green, clean, in
# date) to 1.875 (Tier 1, Red, five-plus events, a year overdue). The boundaries
# are set so that:
#   - a high-criticality gap on a routine Tier 2 Green record reads High, not
#     Critical -- otherwise "Critical" describes the ordinary case and stops
#     carrying information;
#   - the same gap on a Tier 1 Red record with live events reads Critical;
#   - a low-criticality gap on a Tier 3 record reads Low.
# Set too low, every finding on a badly-kept record bands Critical together and
# the register no longer says what to do first, which is the one thing an audit
# reader needs from it.
SEVERITY_BANDS = (
    ("Critical", 1.00),
    ("High", 0.60),
    ("Medium", 0.35),
    ("Low", 0.00),
)

# Target working days to close, by band. Printed against every finding so the
# register doubles as a remediation plan rather than needing one written after.
REMEDIATION_SLA_DAYS = {
    "Critical": 30,
    "High": 60,
    "Medium": 90,
    "Low": 180,
}

# The recommended action, by gap kind. Phrased as an instruction to the named
# owner, because a finding an auditor cannot hand to somebody is an observation.
REMEDIATION_ACTIONS = {
    "field": "Record {item} on the {entity} record.",
    "collection": "Document at least one {item} entry.",
    "collection_partial": "Complete the outstanding {item} ({detail}).",
    "document": "Upload a document under {item} against the {entity}.",
    "document_broken": "Re-upload under {item}: the record cites a file that is "
                       "not in the document store and cannot be produced.",
}

# A document recorded on the register whose file is absent scores above one never
# uploaded at all. Both leave the same hole in the evidence, but the broken
# reference also asserts to a reader that the evidence exists -- an inventory
# that overstates its own coverage is the more serious audit finding, and it will
# not be caught by anyone reading the register alone.
BROKEN_DOC_ESCALATION = 1.15

# Entity-level roll-up. A record is reported as materially incomplete once its
# weighted completeness falls below this: a continuous score turned into a
# statement the committee can act on.
# The knobs a division may set for itself, with the firm-wide value each starts
# from. They live on the division's risk policy (an "audit" section) because that
# is what its MRC already ratifies, and because the audit already reads that policy
# for the rating multipliers — splitting the audit's basis across two places would
# leave nobody able to say what a score was computed against.
#
# The keys are the argument names the escalation helpers take, so the policy is
# read straight into them without a translation table in between.
AUDIT_POLICY_DEFAULTS = {
    "acceptable_at": 0.85,
    "conditional_at": 0.60,
    "untiered_weight": UNTIERED_WEIGHT,
    "unrated_multiplier": UNRATED_MULTIPLIER,
    "event_pressure_per_event": EVENT_PRESSURE_PER_EVENT,
    "event_pressure_cap": EVENT_PRESSURE_CAP,
    "broken_doc_escalation": BROKEN_DOC_ESCALATION,
}

# How each setting is named where the report lists a division's departures from
# the values above -- the same names the Admin -> Risk -> Audit panel uses.
AUDIT_SETTING_LABELS = {
    "acceptable_at": "Acceptable at",
    "conditional_at": "Conditional at",
    "untiered_weight": "Untiered weight",
    "unrated_multiplier": "Unrated multiplier",
    "event_pressure_per_event": "Event pressure, each",
    "event_pressure_cap": "Event pressure, capped at",
    "broken_doc_escalation": "Broken document escalation",
}

COMPLETENESS_ACCEPTABLE_AT = 0.85
COMPLETENESS_CONDITIONAL_AT = 0.60

# The standard the report cites for its scope. Named here so an adopter
# re-pointing the audit at their own framework changes the citation with it.
AUDIT_BASIS = "SR 26-2 (superseding SR 11-7) and PRA SS1/23"
