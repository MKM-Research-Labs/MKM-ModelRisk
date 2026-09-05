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
"""The dashboard's edges: what it says when the usual case does not hold.

The page exists to answer one question, and the ways it can quietly answer it
wrongly are all here — a sentence that runs three counts together, a count that
was filtered but still tallied, an owner handed a blank instruction because the
gap it came from could not be found again.
"""
from __future__ import annotations

from config.governance import (ATTENTION_STATE_LABELS, REASON_BELOW_STANDARD,
                               REASON_COMMITTEE_ACTION_OPEN, REASON_FINDING_OPEN,
                               REASON_REMEDIATION_OVERDUE, REASON_REVIEW_OVERDUE,
                               STATE_ACT, STATE_CLEAR, STATE_ESCALATE)
from src.governance.attention import _rules, collect, queue, summary

AS_OF = "2026-08-24"


def _row(**over):
    return {"completeness": 0.95, "acceptable_at": 0.85, "gaps": [],
            "entity_kind": "Model", "entity_id": "M1", **over}


def _record(**data):
    return {"kind": "Model", "id": "M1", "name": "Alpha", "data": data}


def _item(state, reason):
    return {"state": state, "reason": reason}


# --- how the sentence reads ---------------------------------------------------

def test_three_counts_are_joined_with_a_serial_comma():
    """Without it the last two read as one clause — and these sentences routinely
    list three."""
    detail = summary.verdict([
        _item(STATE_ESCALATE, REASON_BELOW_STANDARD),
        _item(STATE_ACT, REASON_REVIEW_OVERDUE),
        _item(STATE_ACT, REASON_REMEDIATION_OVERDUE),
    ])["detail"]
    assert ", and " in detail
    assert detail.count(",") >= 2


# --- what the breakdown counts ------------------------------------------------

def test_a_breakdown_can_be_narrowed_to_the_states_that_are_being_described():
    """The verdict describes the states owed a response separately from the ones
    already with an owner, so each sentence counts only its own half."""
    items = [_item(STATE_ACT, REASON_BELOW_STANDARD),
             _item(STATE_CLEAR, REASON_FINDING_OPEN)]
    reasons = {r["reason"] for r in summary.breakdown(items, states=[STATE_ACT])}
    assert reasons == {REASON_BELOW_STANDARD}
    assert len(summary.breakdown(items)) == 2


# --- what a state is called ---------------------------------------------------

def test_a_state_is_named_by_the_adopters_own_wording():
    assert _rules.state_label(STATE_ACT) == ATTENTION_STATE_LABELS[STATE_ACT]


def test_a_state_nobody_configured_is_shown_as_itself_rather_than_blank():
    assert _rules.state_label("invented") == "invented"


# --- the instruction handed to an owner ---------------------------------------

def test_a_reason_with_no_matching_gap_carries_no_invented_instruction():
    """The queue hands an owner the audit's own sentence. Where it cannot find
    one, it says nothing rather than wording an instruction of its own."""
    assert queue._gap_action({"gaps": []}, REASON_BELOW_STANDARD) == ""


# --- remediation steps --------------------------------------------------------

def test_a_remediation_step_with_no_date_raises_nothing():
    """Late against what? A step nobody dated is work in progress, and reporting
    it as outstanding would fill the queue with rows nobody can act on."""
    record = _record(remediation_steps=[
        {"item_id": "RM1", "status": "Open", "description": "Rebuild the challenger"}])
    items = queue.build(as_of=AS_OF, records=[record], audit_rows=[_row()])
    assert not [i for i in items if i["reason"] == REASON_REMEDIATION_OVERDUE]


# --- looking once -------------------------------------------------------------

def test_observing_defaults_to_today_and_writes_down_what_the_audit_reports():
    """Called on a schedule, never from a request: the console and the ERM are
    both documented as reads, and a GET that quietly wrote would make both of
    those claims false."""
    result = collect.observe()
    assert set(result) == {"findings", "trend"}
    assert result["trend"]["days"] == 1


def test_a_committee_action_is_outstanding_without_ever_being_late():
    """It belongs to the committee's own cycle, so there is no date to be late
    against — it is open until the committee closes it."""
    items = queue.build(as_of=AS_OF, records=[], audit_rows=[], committee_actions=[
        {"item_id": "AC1", "meeting_id": "MTG1", "description": "Re-run the backtest"}])
    action = next(i for i in items if i["reason"] == REASON_COMMITTEE_ACTION_OPEN)
    assert action["days_over"] is None
