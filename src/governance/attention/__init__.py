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
"""The response queue: what, of everything the registers hold, needs a response.

The completeness audit asks whether each record is complete. This package asks the
question one level up — *"do I need to respond to what I am seeing?"* — and answers
it by classifying every outstanding obligation into one of four states.

It derives no finding of its own. Three of its reasons are an audit gap read under
another name, review currency is whatever the model register already computed, and
the escalation counts are read off the audit rows. The audit is the evidence; this
is the verdict.
"""
from src.governance.attention._rules import (
    below_standard,
    count_label,
    days_overdue,
    due_reason,
    gap_reasons,
    label_of,
    record_reasons,
    review_reason,
    state_label,
    state_of,
    tally,
    worst,
)
from src.governance.attention.collect import (dashboard, observe, records,
                                              unratified_divisions)
from src.governance.attention.history import ages, trend
from src.governance.attention.position import direction, estate, operational
from src.governance.attention.queue import build
from src.governance.attention.summary import breakdown, rows, verdict

__all__ = [
    "ages", "below_standard", "breakdown", "build", "count_label", "dashboard",
    "days_overdue", "direction", "due_reason", "estate", "gap_reasons", "label_of",
    "observe", "operational", "record_reasons", "records", "review_reason", "rows",
    "state_label", "state_of", "tally", "trend", "unratified_divisions", "verdict",
    "worst",
]
