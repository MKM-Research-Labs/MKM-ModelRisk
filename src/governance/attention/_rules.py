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
"""Classifying one obligation into one of the four response states (pure).

No I/O happens here, so the rule an executive is asked to trust — "why is this on
my screen, and why is that not?" — can be checked in isolation from the registers
that feed it.

The module derives no finding of its own. Three of the record-level reasons are an
audit gap read under another name, and review currency is whatever
``compute_review_status`` already told the Models tab. That is the design's central
constraint: the dashboard is the verdict, the audit is the evidence, and a verdict
that quietly recomputed its evidence could disagree with the report a committee
signed.
"""
from __future__ import annotations

from datetime import date
from typing import Any

from config.governance import (
    ATTENTION_PRECEDENCE,
    ATTENTION_REASONS,
    ATTENTION_STATE_LABELS,
    ATTENTION_STATES,
    COMING_DUE_DAYS,
    REASON_BELOW_STANDARD,
    REASON_FINDING_OPEN,
    REASON_FINDING_PAST_SLA,
    REASON_FROM_GAP_KEY,
    REASON_FROM_GAP_KIND,
    REASON_FROM_REVIEW_STATUS,
)
from src.governance.model_inventory.review import compute_review_status


def state_of(reason: str) -> str:
    """The state a reason implies."""
    return ATTENTION_REASONS[reason]["state"]


def label_of(reason: str) -> str:
    """How a reason reads on the row (the adopter's wording)."""
    return ATTENTION_REASONS[reason]["label"]


def action_of(reason: str) -> str:
    """The instruction for a reason the audit does not already word.

    Empty for the three reasons derived from an audit gap: those carry the
    committee's own remediation wording on the gap itself, and a second phrasing
    here is how the dashboard and the signed report start saying different things
    about the same finding.
    """
    return ATTENTION_REASONS[reason].get("action", "")


def is_grouped(reason: str) -> bool:
    """Whether many of these collapse into a single queue row."""
    return bool(ATTENTION_REASONS[reason].get("grouped"))


def group_key_field(reason: str) -> str | None:
    """What a grouped reason collapses ON, or ``None`` for one row per reason.

    ``"owner"`` keeps the name on the row while still collapsing twenty entries
    into three — which is the only way a queue stays both readable and chaseable.
    """
    return ATTENTION_REASONS[reason].get("group_by")


def count_label(reason: str, count: int) -> str:
    """How a count of this reason reads, singular or plural per the count.

    Used both for a collapsed queue row and for the verdict sentence, so the two
    cannot describe the same set of findings in different words.
    """
    singular, plural = ATTENTION_REASONS[reason]["count_label"]
    return (singular if count == 1 else plural).format(count=count)


def worst(reasons) -> str | None:
    """The one obligation a record reports, per the configured precedence.

    A record that is below standard AND missing its sign-off is one record that
    needs one response, not two items on an executive's count. Reasons outside the
    precedence (a committee action, a division's policy) are not record-level and
    never arrive here.
    """
    present = set(reasons)
    for reason in ATTENTION_PRECEDENCE:
        if reason in present:
            return reason
    return None


def days_overdue(due: Any, as_of: str) -> int | None:
    """Days past ``due`` at ``as_of``; negative when still ahead of it.

    ``None`` when either date is absent or unparseable — an unreadable date is not
    an overdue one, and the absence is already a gap in its own right.
    """
    if not due:
        return None
    try:
        return (date.fromisoformat(str(as_of)) - date.fromisoformat(str(due))).days
    except (TypeError, ValueError):
        return None


def due_reason(due: Any, as_of: str, *, overdue: str, soon: str,
               horizon: int = COMING_DUE_DAYS) -> str | None:
    """Classify a plain due date — the shape a committee action has.

    Strictly past is overdue; due today is not, matching ``compute_review_status``
    so a date does not mean one thing on the Models tab and another here.
    """
    over = days_overdue(due, as_of)
    if over is None:
        return None
    if over > 0:
        return overdue
    return soon if -over <= horizon else None


def finding_key(gap: dict) -> str:
    """What identifies one finding across days: the record, and the thing missing.

    Deliberately NOT the severity or the band. Those move as a record's tier or
    rating changes, and a finding whose key moved with them would read as closed and
    reopened on the day somebody re-rated the model — resetting the clock on a gap
    nobody had touched.
    """
    return "|".join(str(gap.get(part) or "")
                    for part in ("entity_kind", "entity_id", "key"))


def past_sla(row: dict, ages: dict | None) -> bool:
    """Whether any gap on this record has outlived its own band's deadline.

    Each band sets its own target days-to-close (``REMEDIATION_SLA_DAYS``, carried
    on the gap), so a Critical finding is late long before a Low one — the same
    thresholds the audit already prints against every finding.

    With no history, nothing is past its deadline. That is not the same as nothing
    being late; it is that we have not looked, and the dashboard says the honest
    thing rather than the flattering one.
    """
    if not ages:
        return False
    for gap in row.get("gaps") or []:
        age = ages.get(finding_key(gap))
        sla = gap.get("sla_days")
        if age is not None and sla is not None and age > sla:
            return True
    return False


def gap_reasons(gaps) -> set[str]:
    """The reasons an audit row's gaps stand for, read through the config mapping."""
    found: set[str] = set()
    for gap in gaps or []:
        for table, key in ((REASON_FROM_GAP_KIND, "kind"), (REASON_FROM_GAP_KEY, "key")):
            reason = table.get(gap.get(key))
            if reason:
                found.add(reason)
    return found


def review_reason(data: dict, as_of: str) -> str | None:
    """The reason a record's next-review date carries, read through the register's
    own classifier so the two screens cannot disagree about the same date."""
    return REASON_FROM_REVIEW_STATUS.get(
        compute_review_status(data.get("next_review_date") or None, as_of))


def record_reasons(row: dict, data: dict, as_of: str, ages: dict | None = None) -> set[str]:
    """Every record-level reason standing against one record.

    ``row`` is the record's completeness-audit row; ``data`` is its register
    document. Both are needed because the audit row scores the record's gaps while
    the register holds the dates the committee set. ``ages`` is the finding history,
    which is what lets an old finding stop counting as merely open.
    """
    reasons = gap_reasons(row.get("gaps"))
    review = review_reason(data, as_of)
    if review:
        reasons.add(review)
    if below_standard(row):
        reasons.add(REASON_BELOW_STANDARD)
    elif row.get("gaps"):
        # Above the standard but not finished. With its owner — unless it has been
        # with its owner longer than the committee's own deadline allows.
        reasons.add(REASON_FINDING_PAST_SLA if past_sla(row, ages)
                    else REASON_FINDING_OPEN)
    return reasons


def below_standard(row: dict) -> bool:
    """Whether a record sits below the threshold its OWN division set.

    Read off the audit row rather than from config: records from several divisions
    sit in one queue, and "is this one acceptable?" cannot be answered by a single
    number looked up at rendering time.
    """
    threshold = row.get("acceptable_at")
    completeness = row.get("completeness")
    if threshold is None or completeness is None:
        return False
    return float(completeness) < float(threshold)


def tally(items) -> dict[str, int]:
    """How many items sit in each state, worst first and every state present.

    An absent key would let a caller render a blank card where the truthful answer
    is a zero, and a zero is the answer an executive most wants to see.
    """
    counts = {state: 0 for state in ATTENTION_STATES}
    for item in items:
        if item.get("state") in counts:
            counts[item["state"]] += 1
    return counts


def state_label(state: str) -> str:
    """What a state is called (the adopter's wording)."""
    return ATTENTION_STATE_LABELS.get(state, state)
