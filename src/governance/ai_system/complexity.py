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
"""Where an AI System sits on the materiality × AI-complexity grid, and what that asks.

Pure: reads the record's fields and the seeded tables in ``config.governance._ai_complexity``
and ``_ai_concepts``, and stores nothing. The position is resolved on READ, as the ML review
scope is, so an edit to a table re-places every system at once with no backfill and nothing
to go stale.

A record missing any of the three inputs is reported as not placed, naming what is missing.
It is never given a default cell: the cell sets how much evidence is asked of the system,
and a guessed cell would ask for less without anybody having decided so.
"""
from __future__ import annotations

from typing import Any

from config.governance._ai_complexity import (AI_COMPLEXITY_RULE, GRID_INTENSITY,
                                              GRID_UNPLACED)
from config.governance._ai_concepts import CONCEPT_AUTONOMY, INTENSITY_CONCEPTS

_INPUTS = (("materiality", "Materiality"), ("ai_autonomy", "Autonomy"),
           ("ai_usage_frequency", "Usage frequency"))


def ai_complexity(autonomy: Any, frequency: Any) -> str | None:
    """The combined complexity level, or ``None`` when the pair is not in the rule."""
    return AI_COMPLEXITY_RULE.get((str(autonomy or ""), str(frequency or "")))


def required_concepts(intensity: str | None, autonomy: Any) -> tuple[int, ...]:
    """The concepts an intensity band asks for, less any this autonomy level is exempt from."""
    wanted = INTENSITY_CONCEPTS.get(intensity or "", ())
    return tuple(n for n in wanted
                 if n not in CONCEPT_AUTONOMY or autonomy in CONCEPT_AUTONOMY[n])


def grid_position(record: dict[str, Any]) -> dict[str, Any]:
    """Place a record: ``{placed, position, materiality, complexity, intensity, concepts,
    missing}``. ``position`` is the readable cell, e.g. ``"High × Medium"``."""
    missing = [label for key, label in _INPUTS if not record.get(key)]
    materiality = record.get("materiality") or None
    autonomy = record.get("ai_autonomy") or None
    complexity = ai_complexity(autonomy, record.get("ai_usage_frequency"))
    intensity = GRID_INTENSITY.get((materiality or "", complexity or ""))
    if not missing and intensity is None:
        # Every input given, but one of them is a value the tables do not know — a
        # vocabulary renamed or extended without the grid following it.
        missing = ["a grid cell for these values"]
    if missing:
        return {"placed": False, "position": GRID_UNPLACED, "materiality": materiality,
                "complexity": complexity, "intensity": None, "concepts": (),
                "missing": missing}
    return {"placed": True, "position": f"{materiality} × {complexity}",
            "materiality": materiality, "complexity": complexity, "intensity": intensity,
            "concepts": required_concepts(intensity, autonomy), "missing": []}


__all__ = ["ai_complexity", "grid_position", "required_concepts"]
