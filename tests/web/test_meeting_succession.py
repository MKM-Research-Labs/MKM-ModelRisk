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
"""Closing a meeting: the record locks, and the next one is scheduled."""
from __future__ import annotations

from src.web.api_mrc._succession import (
    next_date, next_meeting_id, successor_fields, successor_title)


def test_next_date_advances_by_the_committee_interval():
    assert next_date("2026-07-23", "Quarterly") == "2026-10-23"
    assert next_date("2026-07-23", "Monthly") == "2026-08-23"
    assert next_date("2026-07-23", "Annual") == "2027-07-23"


def test_next_date_clamps_to_a_shorter_month():
    """A committee meeting on the 31st must not fall off a 30-day month."""
    assert next_date("2026-01-31", "Monthly") == "2026-02-28"
    assert next_date("2026-08-31", "Monthly") == "2026-09-30"


def test_next_date_falls_back_when_no_frequency_is_set():
    assert next_date("2026-07-23", None) == "2026-10-23"


def test_next_meeting_id_steps_the_period_marker():
    assert next_meeting_id("MTG-PR-Q3", set()) == "MTG-PR-Q4"
    assert next_meeting_id("MRC-2026-M07", set()) == "MRC-2026-M08"


def test_next_meeting_id_rolls_the_period_rather_than_running_past_it():
    assert next_meeting_id("MTG-PR-Q4", set()) == "MTG-PR-Q1"
    assert next_meeting_id("MTG-PR-H2", set()) == "MTG-PR-H1"


def test_next_meeting_id_declines_an_id_already_taken():
    """Returning the current id signals 'no free successor', which the caller
    treats as a reason not to schedule rather than colliding with a real meeting."""
    assert next_meeting_id("MTG-PR-Q3", {"MTG-PR-Q4"}) == "MTG-PR-Q3"


def test_successor_inherits_only_stored_meeting_fields():
    """Division and line of business are derived from the MRC binding, so carrying
    mrc places the successor in the org tree; passing them as fields is rejected."""
    fields = successor_fields({"mrc": "MRC-PR", "division": "PhysicalRisk",
                               "location": "Room A", "status": "Completed"})
    assert fields == {"mrc": "MRC-PR", "location": "Room A"}


def test_successor_title_steps_the_period_and_takes_the_year_from_the_new_date():
    assert successor_title("Division MRC — Q3 2026", "MTG-Q3", "MTG-Q4",
                           "2026-10-23") == "Division MRC — Q4 2026"
    # A period that wraps must not leave the title a year behind its meeting.
    assert successor_title("Division MRC — Q4 2026", "MTG-Q4", "MTG-Q1",
                           "2027-01-23") == "Division MRC — Q1 2027"


def test_successor_title_left_alone_when_it_carries_no_period():
    assert successor_title("Ad-hoc review", "MTG-1", "MTG-2") == "Ad-hoc review"
