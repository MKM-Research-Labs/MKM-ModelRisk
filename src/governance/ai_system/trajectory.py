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
"""Trajectory scoring: did the agent take the path it was supposed to take?

An agentic system's output can be right while the route to it was wrong — three tools
called that should not have been, a credential read on the way past. Scoring only the
answer misses that entirely, which is why an agentic system is measured on its
trajectory as well.

**Applies only where the system can act.** Whether it applies is DERIVED from
``deployment_pattern``, never from a second stored label somebody set: a flag saying "is
agentic" would drift from the pattern the moment one of them was edited, and the two
disagreeing about whether a system can act is the worst possible thing for them to
disagree about.

The distance is graph edit distance over the call sequence — the number of insertions,
deletions and substitutions to turn the observed path into the expected one. Written out
because a reviewer challenging a trajectory score has to be able to follow it, and
because it is the same Levenshtein recurrence every reader already knows.
"""
from __future__ import annotations

from typing import Any, Iterable

from config.governance._ai import DEPLOYMENT_PATTERNS

# The patterns where the system can call something. Derived from the vocabulary rather
# than restated: a pattern added to config that can act must be added here too, and the
# test asserts every pattern is accounted for so a new one cannot be silently omitted.
AGENTIC_PATTERNS = ("Agentic (tool-using)", "Multi-agent")
NON_AGENTIC_PATTERNS = tuple(p for p in DEPLOYMENT_PATTERNS
                             if p not in AGENTIC_PATTERNS)

SKIPPED_NOT_AGENTIC = "not agentic"


def is_agentic(data: dict[str, Any]) -> bool:
    """Whether this system can act, read from its deployment pattern."""
    return str((data or {}).get("deployment_pattern") or "") in AGENTIC_PATTERNS


def edit_distance(observed: Iterable[Any], expected: Iterable[Any]) -> int:
    """Insertions, deletions and substitutions to turn one call sequence into the other.

    Iterative and O(len x len) in time, one row at a time in space. A trajectory is
    short — a handful of tool calls — but a runaway agent's is not, and that is exactly
    the trajectory you want scored rather than the one that blows the stack.
    """
    a, b = list(observed), list(expected)
    previous = list(range(len(b) + 1))
    for i, left in enumerate(a, start=1):
        current = [i]
        for j, right in enumerate(b, start=1):
            current.append(min(previous[j] + 1,          # deletion
                               current[j - 1] + 1,       # insertion
                               previous[j - 1] + (left != right)))  # substitution
        previous = current
    return previous[-1]


def score_trajectory(data: dict[str, Any], observed: Iterable[Any],
                     expected: Iterable[Any]) -> dict[str, Any]:
    """How far the observed path was from the expected one, or why it was not scored.

    ``similarity`` is 1 for an identical path and 0 for one sharing nothing, normalised
    by the longer sequence so a short trajectory and a long one are comparable.
    """
    if not is_agentic(data):
        return {"applies": False, "status": SKIPPED_NOT_AGENTIC, "distance": None,
                "similarity": None,
                "detail": "Trajectory scoring applies to systems that can act. This "
                          "one's deployment pattern is "
                          f"{(data or {}).get('deployment_pattern') or 'unrecorded'}."}
    a, b = list(observed), list(expected)
    if not a and not b:
        return {"applies": True, "status": "no data", "distance": None,
                "similarity": None,
                "detail": "No trajectory recorded, expected or observed."}
    distance = edit_distance(a, b)
    longest = max(len(a), len(b)) or 1
    return {"applies": True, "status": "ok", "distance": distance,
            "similarity": 1 - (distance / longest), "detail": ""}


__all__ = ["AGENTIC_PATTERNS", "NON_AGENTIC_PATTERNS", "SKIPPED_NOT_AGENTIC",
           "edit_distance", "is_agentic", "score_trajectory"]
