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

Two questions, answered in order. The rules in ``config/governance/_mrc_routing.py``
say how far up the committee hierarchy this record must go; the org matching in
``projection`` says which committee at that level covers where it sits. Neither knows
about the other, and neither can invent a committee: everything here resolves to a
committee the institution has actually defined in Admin.

The REASON travels with the answer. A record escalated past its own division's
committee without a stated cause is one somebody will quietly route back, and "because
it is agentic" is an argument a committee can accept or reject — where a silent
escalation is only a surprise.
"""
from __future__ import annotations

from typing import Any

from config.governance._mrc_routing import at_least, rule_for
from src.governance.mrc.projection import committee_at_levels


def route(record_type: str, data: dict[str, Any], refs: dict[str, list]) -> dict[str, Any]:
    """The committee this record must be signed off by, and why.

    Returns the committee, the level it was taken at, the rule that decided, and — where
    the record was escalated above the closest committee that covers it — what it would
    otherwise have gone to. That last field is what lets a screen say "this went to the
    Company MRC rather than the PhysicalRisk Division MRC, because it is agentic".
    """
    division = data.get("division")
    line_of_business = data.get("line_of_business")
    rule = rule_for({**data, "record_type": record_type})

    committee, level = committee_at_levels(
        at_least(rule["level"]), division, line_of_business, refs)
    closest, closest_level = committee_at_levels(
        at_least(None), division, line_of_business, refs)

    # Three outcomes, and they must not be confused on a screen.
    #
    #   routed      a committee took it, possibly the closest one
    #   escalated   a committee took it, above the closest one that covers its org
    #   blocked     a committee covers its org, but NONE is senior enough
    #
    # The third is new with these rules and is the one that reads wrongly if lumped in
    # with "nothing covers this". A firm with no company committee and an agentic
    # system has a gap in its committee structure, not a record filed in the wrong
    # division, and telling it to "set one up under Admin" without saying WHICH level
    # sends somebody to create a duplicate of the committee it already has.
    escalated = committee is not None and closest is not None and closest_level != level
    blocked = committee is None and closest is not None
    return {
        "mrc": committee,
        "level": level,
        "rule": rule["name"],
        "because": rule["because"],
        "required_level": rule["level"],
        "escalated": escalated,
        "blocked": blocked,
        # The committee that covers the org location, wherever that differs from the one
        # the record actually routed to — so a caller can say "rather than X", or
        # "X covers it but is not senior enough", without comparing committees itself.
        "instead_of": closest if (escalated or blocked) else None,
        "instead_of_level": closest_level if (escalated or blocked) else None,
    }


__all__ = ["route"]
