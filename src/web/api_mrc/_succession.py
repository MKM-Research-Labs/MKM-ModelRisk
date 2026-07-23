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
"""Scheduling the successor to a meeting that has just been closed.

A committee that meets on a cycle should never have to remember to create its own
next meeting: closing one schedules the next, an interval ahead, carrying the same
committee binding and the standing agenda. The minutes just filed are attached to
the new meeting's previous-minutes sign-off item, which is the item that exists to
review them — so the next chair opens the meeting with the paper already tabled.

Everything here is best-effort around the close itself: the close has already been
recorded by the time succession runs, and a committee whose frequency is not set
simply gets no successor rather than a failed close.
"""
from __future__ import annotations

import re
from datetime import date

from config.governance import DEFAULT_INTERVAL_MONTHS, MEETING_INTERVAL_MONTHS

# A trailing period marker in a meeting id: Q3, Q4, M07, H1, or a bare number.
_PERIOD = re.compile(r"^(?P<stem>.*?)(?P<letter>[QMH]?)(?P<number>\d+)$")


def next_date(current: str, frequency: str | None) -> str:
    """The successor's date: ``current`` plus the committee's interval.

    Day-of-month is clamped to the target month's length, so a meeting on the 31st
    does not fall off the end of a 30-day month.
    """
    months = MEETING_INTERVAL_MONTHS.get(frequency or "", DEFAULT_INTERVAL_MONTHS)
    start = date.fromisoformat(current)
    total = start.month - 1 + months
    year, month = start.year + total // 12, total % 12 + 1
    if month == 12:
        last = 31
    else:
        last = (date(year + month // 12, month % 12 + 1, 1) - date(year, month, 1)).days
    return date(year, month, min(start.day, last)).isoformat()


def next_meeting_id(current: str, taken: set[str]) -> str:
    """The successor's id, stepping a trailing period marker (``-Q3`` -> ``-Q4``).

    Quarters roll at Q4 rather than running to Q5. An id with no period marker, or
    one whose stepped form is already taken, falls back to appending the date so a
    successor always gets a free id.
    """
    match = _PERIOD.match(current)
    if match:
        letter, number = match.group("letter"), int(match.group("number"))
        limit = {"Q": 4, "H": 2, "M": 12}.get(letter)
        stepped = number + 1
        if limit and stepped > limit:
            stepped = 1
        candidate = f"{match.group('stem')}{letter}{stepped:0{len(match.group('number'))}d}"
        if candidate != current and candidate not in taken:
            return candidate
    return current


# What a successor inherits. Only stored meeting fields appear here: division and
# line of business are derived from the MRC binding, so carrying ``mrc`` places the
# new meeting in the org tree on its own. Attendance, agenda outcomes, minutes and
# status are deliberately not carried — the new meeting starts empty and Scheduled.
INHERITED_FIELDS = ("mrc", "time", "location")


def successor_fields(data: dict) -> dict:
    """The committee binding and standing logistics the successor inherits."""
    return {key: data[key] for key in INHERITED_FIELDS if data.get(key)}


def successor_title(title: str, from_id: str, to_id: str, new_date: str = "") -> str:
    """The successor's title, with the period marker stepped where the old title
    carried one, so ``... — Q3 2026`` becomes ``... — Q4 2026``.

    A year in the title is taken from the successor's own date, so a period that
    wraps (Q4 -> Q1) does not leave the title a year behind its meeting.
    """
    old, new = _PERIOD.match(from_id), _PERIOD.match(to_id)
    if old and new and old.group("letter"):
        marker = old.group("letter") + old.group("number")
        if marker in title:
            title = title.replace(marker, new.group("letter") + new.group("number"))
    if new_date:
        title = re.sub(r"\b(19|20)\d{2}\b", new_date[:4], title)
    return title
