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
"""Computing a variability envelope, and refusing to state one that is not supported.

Pure: percentiles over recorded run scores, plus the rule that binds an envelope to the
configuration that produced it. No I/O.

Two refusals, and both matter more than the arithmetic:

  too few runs        a tight range from three runs reads like a well-behaved system
                      and is the most flattering reading of the least evidence
  configuration moved an envelope measured under a pinned model says nothing about the
                      system after somebody changed the model, and an envelope that
                      quietly outlived its configuration is worse than none
"""
from __future__ import annotations

from typing import Any, Iterable

from config.governance._ai_baseline import (ENVELOPE_NO_RUNS, ENVELOPE_OK,
                                            ENVELOPE_PERCENTILES, ENVELOPE_STALE,
                                            ENVELOPE_TOO_FEW_RUNS, MIN_ENVELOPE_RUNS)


def percentile(values: list[float], p: float) -> float:
    """The p-th percentile by linear interpolation between order statistics.

    Written out rather than imported because the platform has no numerical dependency
    and because a reviewer challenging an envelope has to be able to follow it: sort,
    find the position, interpolate between the two values either side.
    """
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * (p / 100)
    low = int(position)
    high = min(low + 1, len(ordered) - 1)
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


def compute_envelope(scores: Iterable[Any], *, config_version: int | None,
                     percentiles: tuple = ENVELOPE_PERCENTILES) -> dict[str, Any]:
    """The envelope those runs support, or a stated refusal.

    ``config_version`` binds the result to the configuration it was measured under. An
    envelope with no configuration behind it is a number nobody can reproduce.
    """
    values = []
    for score in scores or []:
        try:
            values.append(float(score))
        except (TypeError, ValueError):
            continue

    if not values:
        return {"status": ENVELOPE_NO_RUNS, "runs": 0, "limits": None,
                "config_version": config_version,
                "detail": "No baseline run has been recorded."}
    if len(values) < MIN_ENVELOPE_RUNS:
        # Refused, not narrowed. This is the whole point of the module.
        return {"status": ENVELOPE_TOO_FEW_RUNS, "runs": len(values), "limits": None,
                "config_version": config_version,
                "detail": (f"{len(values)} runs recorded; {MIN_ENVELOPE_RUNS} are "
                           "required before an envelope can be stated. A narrow range "
                           "from few runs reads as a well-behaved system and is the "
                           "most flattering reading of the least evidence.")}

    limits = {str(p): percentile(values, p) for p in percentiles}
    return {"status": ENVELOPE_OK, "runs": len(values), "limits": limits,
            "config_version": config_version,
            "detail": "", "spread": max(limits.values()) - min(limits.values())}


def envelope_status(envelope: dict[str, Any], current_config_version: int | None) -> dict[str, Any]:
    """The envelope as it stands against the configuration in force now.

    An envelope measured under version 2 says nothing about a system now running
    version 3. It is not deleted — it is the record of what was measured, and deleting
    it would lose that — it is marked stale, which is a finding rather than a gap.
    """
    if envelope.get("status") != ENVELOPE_OK:
        return dict(envelope)
    measured_under = envelope.get("config_version")
    if measured_under != current_config_version:
        return {**envelope, "status": ENVELOPE_STALE,
                "detail": (f"Measured under configuration v{measured_under}; the system "
                           f"now runs v{current_config_version}. The envelope describes "
                           "a configuration that is no longer in force.")}
    return dict(envelope)


__all__ = ["compute_envelope", "envelope_status", "percentile"]
