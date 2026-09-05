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
"""Trigger thresholds: the bar a system's behaviour has to clear, property by property.

**Four properties, four thresholds, set independently.** A Tier 1 system's bar on
correctness and its bar on robustness are different questions, and a single severity
level applied to all four is the thing this module exists to prevent. A customer-facing
generative system may warrant a materially tighter robustness threshold — adversarial
resistance — than its predictability threshold, depending on where the actual exposure
sits, and a design that moves them together cannot express that.

Materiality and mission-criticality inform each STARTING POINT rather than fixing all
four at once: the defaults below are where the conversation begins, and the owner and
the escalation chain set each threshold from there.

Nothing here is a measurement. A threshold is what somebody decided was acceptable, and
whether the system clears it is a separate reading — see the measures library. Keeping
the two apart is what lets a committee argue about the bar without arguing about the
number that met it.
"""
from __future__ import annotations

from typing import Any

# The four properties, and what each is asking. Named rather than free text because a
# trigger register whose properties differ per record cannot be reported across the
# estate — which is the only reason to keep one.
PROPERTY_CORRECTNESS = "correctness"
PROPERTY_CONSISTENCY = "consistency"
PROPERTY_ROBUSTNESS = "robustness"
PROPERTY_PREDICTABILITY = "predictability"

TRIGGER_PROPERTIES = (PROPERTY_CORRECTNESS, PROPERTY_CONSISTENCY,
                      PROPERTY_ROBUSTNESS, PROPERTY_PREDICTABILITY)

PROPERTY_NOTES = {
    PROPERTY_CORRECTNESS: "Is the answer right, measured against something that knows.",
    PROPERTY_CONSISTENCY: "Does the same input give the same answer, within the "
                          "variability envelope agreed at baseline.",
    PROPERTY_ROBUSTNESS: "Does it hold up under adversarial or malformed input — "
                         "including input that arrives as content and is read as "
                         "instruction.",
    PROPERTY_PREDICTABILITY: "Is its confidence calibrated: does it know when it does "
                             "not know.",
}

# Where the conversation starts, by mission-criticality band score. These are FLOORS a
# committee moves, not settings the platform applies: a system that never reaches the
# committee keeps the default and that fact is visible, which is the point of having
# one at all.
#
# Read as "the proportion of checks that must pass". The three bands are the seeded
# vocabulary; a band an institution adds resolves to the last entry, deliberately —
# an unrecognised tier should not silently get the loosest bar.
DEFAULT_THRESHOLDS_BY_TIER: dict[str, dict[str, float]] = {
    "1": {PROPERTY_CORRECTNESS: 0.95, PROPERTY_CONSISTENCY: 0.90,
          PROPERTY_ROBUSTNESS: 0.95, PROPERTY_PREDICTABILITY: 0.85},
    "2": {PROPERTY_CORRECTNESS: 0.90, PROPERTY_CONSISTENCY: 0.85,
          PROPERTY_ROBUSTNESS: 0.85, PROPERTY_PREDICTABILITY: 0.75},
    "3": {PROPERTY_CORRECTNESS: 0.80, PROPERTY_CONSISTENCY: 0.75,
          PROPERTY_ROBUSTNESS: 0.75, PROPERTY_PREDICTABILITY: 0.65},
}
_FALLBACK_TIER = "1"

# What happens when a threshold is breached. A trigger with no stated consequence is a
# metric, and the register exists to hold consequences.
FALLBACK_STATES = ("Continue and note", "Escalate to the owner",
                   "Escalate to the committee", "Human review every output",
                   "Suspend the system")
DEFAULT_FALLBACK = "Escalate to the owner"


def default_thresholds(tier: Any) -> dict[str, float]:
    """The starting point for a record at this mission-criticality band.

    An unrecognised or missing tier gets the STRICTEST defaults, not the loosest. A
    record nobody has rated is one nobody has thought about, and the safe reading of
    that is not to relax the bar.
    """
    return dict(DEFAULT_THRESHOLDS_BY_TIER.get(str(tier or ""),
                                               DEFAULT_THRESHOLDS_BY_TIER[_FALLBACK_TIER]))


def is_property(name: str) -> bool:
    return name in TRIGGER_PROPERTIES


__all__ = ["DEFAULT_FALLBACK", "DEFAULT_THRESHOLDS_BY_TIER", "FALLBACK_STATES",
           "PROPERTY_CONSISTENCY", "PROPERTY_CORRECTNESS", "PROPERTY_NOTES",
           "PROPERTY_PREDICTABILITY", "PROPERTY_ROBUSTNESS", "TRIGGER_PROPERTIES",
           "default_thresholds", "is_property"]
