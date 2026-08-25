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
"""Unit tests for the dashboard's response rule (pure).

The rule an executive is asked to trust is "why is this on my screen, and why is
that not?". These tests assert that rule directly, and in particular the two
properties that make the page worth having: one record contributes one item, and
the dashboard never invents a finding or a deadline the registers do not hold.
"""
from __future__ import annotations

import pytest

from config.governance import (
    ATTENTION_REASONS,
    ATTENTION_STATES,
    COMING_DUE_DAYS,
    EVENTS_WINDOW_DAYS,
    REASON_BELOW_STANDARD,
    REASON_COMMITTEE_ACTION_OPEN,
    REASON_EVIDENCE_MISSING,
    REASON_FINDING_OPEN,
    REASON_POLICY_UNRATIFIED,
    REASON_REMEDIATION_DUE_SOON,
    REASON_REMEDIATION_OVERDUE,
    REASON_REVIEWER_NOT_INDEPENDENT,
    REASON_REVIEW_DUE_SOON,
    REASON_REVIEW_OVERDUE,
    REASON_SIGNOFF_MISSING,
    REVIEW_DUE_SOON_DAYS,
    STATE_ACT,
    STATE_CLEAR,
    STATE_ESCALATE,
    STATE_MONITOR,
)
from src.governance.attention import _rules, position, queue, summary

AS_OF = "2026-08-24"
CLEAN = {"completeness": 0.95, "acceptable_at": 0.85, "gaps": [],
         "entity_kind": "Model", "entity_id": "M1"}


def _row(**over):
    return {**CLEAN, **over}


def _record(rid="M1", kind="Model", **data):
    return {"kind": kind, "id": rid, "name": data.get("name", "Alpha"), "data": data}


def _gap(kind="field", key="owner", action="Record owner."):
    return {"kind": kind, "key": key, "action": action}


# --- the horizon is not a second horizon -----------------------------------

def test_coming_due_reuses_the_registers_own_due_soon_window():
    """Two horizons would let the Models tab call a review Due Soon on a day the
    dashboard still counted it clear, with nothing on either screen to say why."""
    assert COMING_DUE_DAYS == REVIEW_DUE_SOON_DAYS


# --- reading the audit rather than re-deriving it ---------------------------

@pytest.mark.parametrize("gap,expected", [
    (_gap(kind="rule", key="reviewer_independence"), REASON_REVIEWER_NOT_INDEPENDENT),
    (_gap(kind="document_broken", key="Validation"), REASON_EVIDENCE_MISSING),
    (_gap(key="mrc_signoff_date"), REASON_SIGNOFF_MISSING),
])
def test_a_reason_is_an_audit_gap_under_another_name(gap, expected):
    assert _rules.gap_reasons([gap]) == {expected}


def test_a_gap_the_dashboard_does_not_speak_for_raises_nothing():
    assert _rules.gap_reasons([_gap(key="materiality")]) == set()


def test_the_instruction_travels_on_the_gap_not_the_reason_table():
    """The three gap-derived reasons carry no wording of their own, so the queue
    hands an owner the same sentence the signed report does."""
    for reason in (REASON_REVIEWER_NOT_INDEPENDENT, REASON_EVIDENCE_MISSING,
                   REASON_SIGNOFF_MISSING):
        assert "action" not in ATTENTION_REASONS[reason]


# --- dates ------------------------------------------------------------------

@pytest.mark.parametrize("due,expected", [
    ("2026-08-23", REASON_REVIEW_OVERDUE),
    ("2026-08-24", REASON_REVIEW_DUE_SOON),      # due today is not yet overdue
    ("2026-09-20", REASON_REVIEW_DUE_SOON),
    ("2026-12-01", None),
    ("", None),
])
def test_review_currency_follows_the_registers_own_classifier(due, expected):
    assert _rules.review_reason({"next_review_date": due}, AS_OF) == expected


@pytest.mark.parametrize("due,expected", [
    ("2026-08-01", REASON_REMEDIATION_OVERDUE),
    ("2026-08-24", REASON_REMEDIATION_DUE_SOON),
    ("2027-01-01", None),
    (None, None),
    ("not-a-date", None),
])
def test_a_remediation_step_is_late_only_against_a_date_somebody_set(due, expected):
    assert _rules.due_reason(due, AS_OF, overdue=REASON_REMEDIATION_OVERDUE,
                             soon=REASON_REMEDIATION_DUE_SOON) == expected


def test_a_committee_action_can_be_outstanding_but_never_late():
    """An MRC action is agreed without a target date, so calling one overdue would
    put a deadline in front of an executive that no committee ever set."""
    assert ATTENTION_REASONS[REASON_COMMITTEE_ACTION_OPEN]["state"] == STATE_MONITOR


# --- the threshold is the division's, not a global one ----------------------

def test_below_standard_reads_the_threshold_carried_on_the_row():
    assert _rules.below_standard(_row(completeness=0.80, acceptable_at=0.85))
    assert not _rules.below_standard(_row(completeness=0.80, acceptable_at=0.75))


def test_a_row_missing_either_number_is_not_reported_as_below():
    assert not _rules.below_standard(_row(acceptable_at=None))
    assert not _rules.below_standard(_row(completeness=None))


# --- one record, one item ---------------------------------------------------

def test_a_record_reports_only_its_worst_obligation():
    """Otherwise the executive's count measures how many ways one record is behind
    rather than how many records are."""
    reasons = {REASON_SIGNOFF_MISSING, REASON_BELOW_STANDARD, REASON_REVIEW_OVERDUE}
    assert _rules.worst(reasons) == REASON_SIGNOFF_MISSING


def test_a_record_with_nothing_against_it_produces_no_item():
    assert _rules.worst(set()) is None
    assert _rules.record_reasons(_row(), {}, AS_OF) == set()


def test_an_incomplete_record_is_below_standard_rather_than_merely_open():
    reasons = _rules.record_reasons(
        _row(completeness=0.4, gaps=[_gap()]), {}, AS_OF)
    assert REASON_BELOW_STANDARD in reasons and REASON_FINDING_OPEN not in reasons


def test_a_record_above_the_standard_with_gaps_is_with_its_owner():
    reasons = _rules.record_reasons(_row(gaps=[_gap()]), {}, AS_OF)
    assert reasons == {REASON_FINDING_OPEN}
    assert _rules.state_of(REASON_FINDING_OPEN) == STATE_CLEAR


def test_one_record_yields_one_queue_row_however_many_ways_it_is_behind():
    row = _row(completeness=0.3, gaps=[_gap(key="mrc_signoff_date"), _gap()])
    items = queue.build(as_of=AS_OF, records=[_record(next_review_date="2020-01-01")],
                        audit_rows=[row])
    assert len(items) == 1
    assert items[0]["reason"] == REASON_SIGNOFF_MISSING


def test_a_record_with_no_audit_row_is_skipped_rather_than_reported_clear():
    assert queue.build(as_of=AS_OF, records=[_record()], audit_rows=[]) == []


# --- the other three kinds of item -----------------------------------------

def test_a_remediation_step_is_its_own_item_with_its_own_owner():
    record = _record(remediation_steps=[
        {"item_id": "RM1", "due_date": "2026-01-01", "owner": "J. Patel",
         "description": "Rebuild the challenger", "status": "Open"}])
    items = queue.build(as_of=AS_OF, records=[record], audit_rows=[_row()])
    step = next(i for i in items if i["reason"] == REASON_REMEDIATION_OVERDUE)
    assert step["owner"] == "J. Patel" and step["days_over"] == 235


def test_a_closed_remediation_step_raises_nothing():
    record = _record(remediation_steps=[
        {"item_id": "RM1", "due_date": "2026-01-01", "status": "Closed"}])
    items = queue.build(as_of=AS_OF, records=[record], audit_rows=[_row()])
    assert not [i for i in items if i["reason"] == REASON_REMEDIATION_OVERDUE]


def test_several_owners_on_one_step_are_all_named():
    """Showing one of three names sends the chase to the wrong person."""
    record = _record(remediation_steps=[
        {"item_id": "RM1", "due_date": "2026-01-01", "status": "Open",
         "owner": ["A. Okonjo", "R. Ndlovu"]}])
    items = queue.build(as_of=AS_OF, records=[record], audit_rows=[_row()])
    assert items[-1]["owner"] == "A. Okonjo, R. Ndlovu"


def test_an_unratified_division_is_an_escalation_naming_its_committee():
    items = queue.build(as_of=AS_OF, records=[], audit_rows=[], unratified_divisions=[
        {"division": "Retail", "committee": "Retail MRC", "chair": "A. Okonjo"}])
    assert items[0]["state"] == STATE_ESCALATE
    assert items[0]["reason"] == REASON_POLICY_UNRATIFIED
    assert items[0]["committee"] == "Retail MRC" and items[0]["owner"] == "A. Okonjo"


def test_an_open_committee_action_carries_its_committee_and_no_date():
    items = queue.build(as_of=AS_OF, records=[], audit_rows=[], committee_actions=[
        {"item_id": "A-12", "description": "Supply closure evidence",
         "mrc": "Group MRC", "meeting_id": "MRC-1", "owner": "R. Ndlovu"}])
    assert items[0]["state"] == STATE_MONITOR and items[0]["due"] is None


# --- the verdict ------------------------------------------------------------

def test_an_empty_register_answers_the_question_with_no():
    v = summary.verdict([])
    assert v["response_required"] is False
    assert v["state"] == STATE_CLEAR
    assert v["counts"] == {state: 0 for state in ATTENTION_STATES}


def test_every_state_is_counted_even_at_zero():
    """A blank card where the truthful answer is a zero is the one number an
    executive most wants to see, withheld."""
    counts = _rules.tally([{"state": STATE_ACT}])
    assert set(counts) == set(ATTENTION_STATES) and counts[STATE_ESCALATE] == 0


def test_the_verdict_takes_the_worst_state_present_not_an_average():
    items = [{"state": STATE_ESCALATE, "reason": REASON_POLICY_UNRATIFIED},
             {"state": STATE_ACT, "reason": REASON_REVIEW_OVERDUE},
             {"state": STATE_ACT, "reason": REASON_REVIEW_OVERDUE}]
    v = summary.verdict(items)
    assert v["response_required"] is True and v["state"] == STATE_ESCALATE
    assert v["headline"] == "3 items need your response."


def test_a_single_item_reads_as_one_not_as_1_items():
    v = summary.verdict([{"state": STATE_ACT, "reason": REASON_REVIEW_OVERDUE}])
    assert v["headline"] == "1 item needs your response."
    assert "1 review is overdue" in v["detail"]


def test_items_with_owners_do_not_count_against_the_reader():
    items = [{"state": STATE_CLEAR, "reason": REASON_FINDING_OPEN} for _ in range(14)]
    v = summary.verdict(items)
    assert v["response_required"] is False
    assert "14 records carry open findings" in v["detail"]


def test_the_breakdown_is_assembled_from_the_configured_wording():
    rows = summary.breakdown([{"state": STATE_ACT, "reason": REASON_BELOW_STANDARD}] * 12)
    assert rows == [{"reason": REASON_BELOW_STANDARD, "state": STATE_ACT, "count": 12,
                     "label": "12 records are below the acceptable standard"}]


# --- the queue's rows -------------------------------------------------------

def test_a_grouped_reason_collapses_to_one_row_carrying_its_members():
    items = [{"state": STATE_ACT, "reason": REASON_BELOW_STANDARD, "id": f"x{i}",
              "reason_label": "", "entity": None, "owner": "", "due": None,
              "days_over": None} for i in range(12)]
    drawn = summary.rows(items)
    assert drawn["total_rows"] == 1 and drawn["total_items"] == 12
    assert drawn["rows"][0]["reason_label"] == "12 records are below the acceptable standard"
    assert len(drawn["rows"][0]["members"]) == 12


def test_an_ungrouped_reason_keeps_one_row_each():
    items = [{"state": STATE_ACT, "reason": REASON_REVIEW_OVERDUE, "id": f"x{i}",
              "reason_label": "", "entity": None, "owner": "", "due": None,
              "days_over": None} for i in range(3)]
    assert summary.rows(items)["total_rows"] == 3


def test_a_reason_grouped_by_owner_keeps_the_name_that_makes_it_chaseable():
    """Twenty near-identical rows bury the findings that are singular; collapsing
    them to nothing takes away the one thing an executive can act on. One row per
    person is both."""
    items = [{"state": STATE_ACT, "reason": REASON_REMEDIATION_OVERDUE, "id": f"x{i}",
              "reason_label": "", "entity": {"id": f"M{i % 4}"},
              "owner": ["A. Okonjo", "R. Ndlovu"][i % 2], "due": None,
              "days_over": i * 10} for i in range(10)]
    drawn = summary.rows(items)
    assert drawn["total_rows"] == 2 and drawn["total_items"] == 10
    owners = sorted(r["owner"] for r in drawn["rows"])
    assert owners == ["A. Okonjo", "R. Ndlovu"]
    worst = max(r["days_over"] for r in drawn["rows"])
    assert worst == 90                      # the group still says how bad it is
    assert all(r["records"] > 1 for r in drawn["rows"])


def test_truncation_is_declared_rather_than_silent():
    items = [{"state": STATE_ACT, "reason": REASON_REVIEW_OVERDUE, "id": f"x{i}",
              "reason_label": "", "entity": None, "owner": "", "due": None,
              "days_over": None} for i in range(5)]
    drawn = summary.rows(items, cap=2)
    assert drawn["truncated"] is True
    assert drawn["returned"] == 2 and drawn["total_rows"] == 5


# --- the position feeds -----------------------------------------------------

def test_the_estate_names_the_absent_tier_rather_than_dropping_it():
    shape = position.estate([_record(tier=1), _record("M2"), _record("M3", rag_rating="Red")])
    assert shape["by_tier"] == {"1": 1, "untiered": 2}
    assert shape["by_rating"] == {"Red": 1, "unrated": 2}


def test_the_operational_feed_reads_failures_off_the_audit_row():
    feed = position.operational(
        [_row(events_in_window=2), _row(events_in_window=0)],
        [{"state": STATE_ESCALATE, "reason": REASON_SIGNOFF_MISSING}])
    assert feed["failures_in_window"] == 2 and feed["records_with_failures"] == 1
    assert feed["window_days"] == EVENTS_WINDOW_DAYS
    assert feed["control_breaches"] == 1


def test_direction_reports_a_count_ratio_not_an_invented_average():
    feed = position.direction([_row(), _row(completeness=0.1), _row(completeness=0.2)])
    assert feed["records_meeting_standard"] == 1
    assert feed["share_meeting_standard"] == pytest.approx(1 / 3, rel=1e-3)


def test_no_history_is_reported_as_none_rather_than_as_flat():
    """A strategic view that cannot tell "no history yet" from "flat" would read a
    new install as a stable one."""
    assert position.direction([_row()])["trend"] is None


def test_a_group_of_one_is_not_collapsed():
    """Collapsing it would read "1 record is below the standard" and then decline
    to say which — the opposite of what the row is for."""
    item = {"state": STATE_ACT, "reason": REASON_BELOW_STANDARD, "id": "x",
            "reason_label": "Below the standard", "entity": {"id": "M1"},
            "owner": "J. Patel", "due": None, "days_over": None}
    row = summary.rows([item])["rows"][0]
    assert row["grouped"] is False
    assert row["entity"] == {"id": "M1"} and row["owner"] == "J. Patel"
