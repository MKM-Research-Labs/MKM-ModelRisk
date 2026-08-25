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
"""Tests for the finding history: what lets a finding be aged and a trend drawn.

Two properties carry the whole feature and both are easy to get quietly wrong. A
finding's identity must not move when its severity does, or a re-rated model would
look like it had closed and reopened everything on it. And an unobserved finding
must not read as a new one, because "we have not looked yet" is not a measurement.
"""
from __future__ import annotations

from src.governance.attention import _rules, history

AS_OF = "2026-08-25"
LATER = "2026-09-25"


def _gap(entity="M1", key="owner", *, band="High", severity=0.9, sla=60, kind="Model"):
    return {"entity_kind": kind, "entity_id": entity, "entity_name": "Alpha",
            "key": key, "label": "Owner", "band": band, "severity": severity,
            "sla_days": sla}


def _rows(*gaps):
    return [{"entity_kind": "Model", "entity_id": "M1", "gaps": list(gaps)}]


# --- identity ---------------------------------------------------------------

def test_a_findings_identity_is_the_record_and_the_thing_missing():
    assert _rules.finding_key(_gap()) == "Model|M1|owner"


def test_re_rating_a_record_does_not_change_what_its_findings_are():
    """Severity moves with tier and rating. If it were part of the key, re-rating a
    model would close every finding on it and open an identical set the same day,
    resetting every clock."""
    before = _rules.finding_key(_gap(band="Low", severity=0.3, sla=180))
    after = _rules.finding_key(_gap(band="Critical", severity=1.4, sla=30))
    assert before == after


def test_two_records_missing_the_same_field_are_two_findings():
    assert _rules.finding_key(_gap("M1")) != _rules.finding_key(_gap("M2"))


# --- ageing -----------------------------------------------------------------

def test_nothing_is_past_its_deadline_when_nothing_has_been_observed():
    """Not the same as nothing being late: it is that we have not looked, and the
    dashboard says the honest thing rather than the flattering one."""
    assert _rules.past_sla({"gaps": [_gap()]}, None) is False
    assert _rules.past_sla({"gaps": [_gap()]}, {}) is False


def test_a_finding_is_late_only_once_it_outlives_its_own_bands_deadline():
    gap = _gap(sla=60)
    key = _rules.finding_key(gap)
    assert _rules.past_sla({"gaps": [gap]}, {key: 59}) is False
    assert _rules.past_sla({"gaps": [gap]}, {key: 60}) is False
    assert _rules.past_sla({"gaps": [gap]}, {key: 61}) is True


def test_bands_carry_different_deadlines_so_a_critical_finding_is_late_sooner():
    critical, low = _gap(key="a", sla=30), _gap(key="b", sla=180)
    at_100 = {_rules.finding_key(critical): 100, _rules.finding_key(low): 100}
    assert _rules.past_sla({"gaps": [critical]}, at_100) is True
    assert _rules.past_sla({"gaps": [low]}, at_100) is False


def test_one_late_finding_is_enough_to_report_the_record():
    gaps = [_gap(key="a", sla=180), _gap(key="b", sla=30)]
    ages = {_rules.finding_key(gaps[0]): 10, _rules.finding_key(gaps[1]): 90}
    assert _rules.past_sla({"gaps": gaps}, ages) is True


# --- what the observer writes ----------------------------------------------

def test_the_observer_keys_every_gap_it_can_see():
    seen = history._open_findings(_rows(_gap(key="a"), _gap(key="b")))
    assert set(seen) == {"Model|M1|a", "Model|M1|b"}
    assert seen["Model|M1|a"]["sla_days"] == 60


def test_a_record_with_no_gaps_contributes_nothing():
    assert history._open_findings([{"entity_kind": "Model", "entity_id": "M1",
                                    "gaps": []}]) == {}


def test_a_stored_date_reads_the_same_whichever_way_the_driver_returned_it():
    from datetime import date
    assert history._iso(date(2026, 8, 25)) == history._iso("2026-08-25") == AS_OF
    assert history._iso(None) == ""


# --- the round trip, against a real database --------------------------------

def test_observing_twice_in_a_day_does_not_double_count():
    """A restart must not make a finding look like two, or a day like two days."""
    first = history.observe(AS_OF, _rows(_gap()), {"records_audited": 1})
    second = history.observe(AS_OF, _rows(_gap()), {"records_audited": 1})
    assert first["findings"]["opened"] == 1
    assert second["findings"]["opened"] == 0          # already known
    assert second["trend"]["days"] == 1               # still one day observed


def test_a_finding_ages_from_when_it_was_first_seen_not_from_today():
    history.observe(AS_OF, _rows(_gap()), {})
    history.observe(LATER, _rows(_gap()), {})
    assert history.ages(LATER)["Model|M1|owner"] == 31


def test_a_finding_that_stops_appearing_is_closed_and_stops_ageing():
    history.observe(AS_OF, _rows(_gap()), {})
    closed = history.observe(LATER, [{"entity_kind": "Model", "entity_id": "M1",
                                      "gaps": []}], {})
    assert closed["findings"]["closed"] == 1
    assert "Model|M1|owner" not in history.ages(LATER)


def test_a_finding_that_comes_back_keeps_its_original_clock():
    """Otherwise a record escapes its deadline by being briefly fixed."""
    history.observe(AS_OF, _rows(_gap()), {})
    history.observe("2026-09-01", [{"entity_kind": "Model", "entity_id": "M1",
                                    "gaps": []}], {})
    history.observe(LATER, _rows(_gap()), {})
    assert history.ages(LATER)["Model|M1|owner"] == 31


def test_no_history_reports_none_rather_than_an_empty_series():
    """A strategic view that cannot tell "no history yet" from "flat" would read a
    new install as a stable one."""
    assert history.trend() is None


def test_the_trend_comes_back_oldest_first_with_its_dates():
    history.observe(AS_OF, [], {"records_meeting_standard": 1})
    history.observe(LATER, [], {"records_meeting_standard": 2})
    series = history.trend()
    assert [row["as_of"] for row in series] == [AS_OF, LATER]
    assert [row["records_meeting_standard"] for row in series] == [1, 2]
