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
"""Which committee a record routes to, and the reason it routes there.

**Every record is managed at the MRC it is assigned to.** A model, an ML Application
and an AI System are each assigned to a division and a line of business, and the most
specific committee covering that org location signs it off. There is no escalation and
no company-level committee to reach: where the record sits IS the answer, for all three
record types alike.

An escalation ladder briefly lived here — added 2026-09-05, removed 2026-09-06. It
raised mission-critical and agentic records to a company committee, which nobody had
asked for and which this firm's structure does not have. It blocked two live tier-1
models that had routed to their division committee for months, because a rule invented
for a new record type reached back and changed how existing models were governed. If an
institution ever does want a record to go somewhere other than its own committee, that
is a governance decision for the firm to state — not one inferred from a record's
attributes.

The REASON still travels with the answer, because a screen has to say why this
committee and not another, and "nothing covers this org location" has to read
differently from "no committee exists at all".
"""
from __future__ import annotations

from typing import Any

from config.governance._reference import MRC_LEVELS_CLOSEST_FIRST
from src.governance.mrc.projection import committee_at_levels


def route(record_type: str, data: dict[str, Any], refs: dict[str, list]) -> dict[str, Any]:
    """The committee this record is signed off by, and why.

    ``record_type`` is accepted and deliberately unused: the three governed record
    types route identically, and a signature that took one would invite a caller to
    believe otherwise.
    """
    committee, level = committee_at_levels(
        MRC_LEVELS_CLOSEST_FIRST, data.get("division"), data.get("line_of_business"), refs)
    return {
        "mrc": committee,
        "level": level,
        "because": ("The most specific committee covering this record's division and "
                    "line of business."),
        # Nothing covers this record's org location. Not an escalation problem: either
        # the record is filed under a division nobody has a committee for, or the
        # committee has been archived.
        "blocked": committee is None,
    }


__all__ = ["route"]
