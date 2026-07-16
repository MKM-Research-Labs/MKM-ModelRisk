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
"""Model review status derived from the next-review date (pure)."""
from __future__ import annotations

from datetime import date

from config.governance import REVIEW_DUE_SOON_DAYS, REVIEW_UPCOMING_DAYS


def compute_review_status(next_review_date: str | None, as_of: str) -> str:
    """Classify a model's review currency relative to ``as_of`` (ISO dates)."""
    if not next_review_date:
        return "Not Scheduled"
    days = (date.fromisoformat(next_review_date) - date.fromisoformat(as_of)).days
    if days < 0:
        return "Overdue"
    if days <= REVIEW_DUE_SOON_DAYS:
        return "Due Soon"
    if days <= REVIEW_UPCOMING_DAYS:
        return "Upcoming"
    return "On Track"
