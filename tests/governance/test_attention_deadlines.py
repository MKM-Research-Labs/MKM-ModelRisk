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
"""When a completeness finding falls due — the dates the dashboard and the record quote.

The history ages a finding; the band sets its deadline. These tests pin the date
arithmetic between the two, and that a past-deadline row on the dashboard now says
which finding is late and since when rather than only that one is.
"""
from __future__ import annotations

from config.governance import COMING_DUE_DAYS, FINDING_DEADLINE_LABELS
from src.governance.attention import _rules, deadlines, queue, summary

AS_OF = "2026-11-03"


def _gap(key="materiality_rationale", label="Materiality rationale", *, sla=60,
         entity="M1", band="High"):
    return {"entity_kind": "Model", "entity_id": entity, "key": key, "label": label,
            "band": band, "sla_days": sla, "action": "Record it.", "kind": "field"}


def _ages(*pairs):
    return {_rules.finding_key(gap): age for gap, age in pairs}


def _one(gap, age):
    return deadlines.gap_deadlines([gap], _ages((gap, age)), AS_OF)[0]


# --- the arithmetic ---------------------------------------------------------

def test_the_due_date_is_first_seen_plus_the_bands_deadline():
    # Seen first on 25 August, a High finding is due 60 days later.
    f = _one(_gap(), 70)
    assert f["first_seen"] == "2026-08-25"
    assert f["due"] == "2026-10-24"
    assert f["days_over"] == 10
    assert f["status"] == "overdue"


def test_due_today_is_not_yet_late():
    """Strictly past, as ``past_sla`` counts it, so the two never disagree."""
    f = _one(_gap(), 60)
    assert f["days_over"] == 0 and f["status"] == "due_soon"
    assert _rules.past_sla({"gaps": [_gap()]}, _ages((_gap(), 60))) is False


def test_a_finding_inside_the_horizon_is_due_soon_and_beyond_it_is_open():
    assert _one(_gap(), 60 - COMING_DUE_DAYS)["status"] == "due_soon"
    assert _one(_gap(), 60 - COMING_DUE_DAYS - 1)["status"] == "open"


def test_a_finding_never_observed_has_no_date_rather_than_an_invented_one():
    f = deadlines.gap_deadlines([_gap()], {}, AS_OF)[0]
    assert f["first_seen"] is None and f["due"] is None and f["days_over"] is None
    assert f["status"] == "unobserved"
    assert deadlines.gap_deadlines([_gap()], None, AS_OF)[0]["status"] == "unobserved"


def test_a_gap_without_a_band_deadline_is_left_undated():
    gap = {**_gap(), "sla_days": None}
    assert _one(gap, 90)["due"] is None


def test_every_status_reads_through_the_adopters_wording():
    for gap, age in ((_gap(), 90), (_gap(), 60), (_gap(), 1)):
        f = _one(gap, age)
        assert f["status_label"] == FINDING_DEADLINE_LABELS[f["status"]]


def test_the_list_runs_worst_first():
    late, later, fresh, unseen = (_gap("a", "A"), _gap("b", "B"), _gap("c", "C"),
                                  _gap("d", "D"))
    ages = _ages((late, 70), (later, 90), (fresh, 1))
    order = [f["key"] for f in deadlines.gap_deadlines(
        [unseen, fresh, late, later], ages, AS_OF)]
    assert order == ["b", "a", "c", "d"]


# --- what the dashboard row says --------------------------------------------

def test_a_record_with_nothing_late_has_no_overdue_date():
    assert deadlines.overdue_summary([_gap()], _ages((_gap(), 5)), AS_OF) == {
        "due": None, "days_over": None, "detail": ""}


def test_the_row_carries_the_earliest_due_date_and_the_furthest_over():
    rationale, vqs = _gap(), _gap("validation_questions", "Validation questions", sla=90)
    out = deadlines.overdue_summary([rationale, vqs],
                                    _ages((rationale, 70), (vqs, 99)), AS_OF)
    assert out["due"] == "2026-10-24"
    assert out["days_over"] == 10
    assert "Materiality rationale (due 2026-10-24)" in out["detail"]
    assert "Validation questions (due 2026-10-25)" in out["detail"]


def _record(rid="M1"):
    return {"kind": "Model", "id": rid, "name": "Alpha", "data": {"owner": "bob"}}


def _row(*gaps, rid="M1"):
    return {"entity_kind": "Model", "entity_id": rid, "completeness": 0.95,
            "acceptable_at": 0.85, "gaps": list(gaps)}


def test_a_past_deadline_item_names_its_date_and_its_late_findings():
    gap = _gap()
    items = queue.build(as_of=AS_OF, records=[_record()], audit_rows=[_row(gap)],
                        ages=_ages((gap, 70)))
    [item] = items
    assert item["reason"] == "finding_past_sla"
    assert item["due"] == "2026-10-24" and item["days_over"] == 10
    assert "Materiality rationale" in item["detail"]


def test_a_finding_still_inside_its_deadline_carries_no_date():
    gap = _gap()
    [item] = queue.build(as_of=AS_OF, records=[_record()], audit_rows=[_row(gap)],
                         ages=_ages((gap, 5)))
    assert item["reason"] == "finding_open"
    assert item["due"] is None and item["days_over"] is None


def test_a_collapsed_row_shows_the_earliest_due_date_of_its_members():
    one, two = _gap(entity="M1"), _gap(entity="M2")
    items = queue.build(
        as_of=AS_OF, records=[_record("M1"), _record("M2")],
        audit_rows=[_row(one, rid="M1"), _row(two, rid="M2")],
        ages=_ages((one, 70), (two, 65)))
    [group] = [r for r in summary.rows(items)["rows"] if r["grouped"]]
    assert group["due"] == "2026-10-24"
    assert group["days_over"] == 10
