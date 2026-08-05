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
"""The seed risk policy, derived from the existing ``config.governance`` constants.

This is the policy an institution starts with before an admin edits anything, so it
reproduces today's behaviour EXACTLY: the same Materiality/Complexity/Mission-Criticality
bands, the same Materiality×Complexity→rating grid per Mission-Criticality band (from
``RISK_HEATMAP_BY_TIER``), and the same completeness multipliers (from ``RAG_MULTIPLIERS``).

Every band is ``{name, colour, explanation, score}``. Mission Criticality replaces the old
"Tier"; its band scores are the legacy tier integers (1/2/3) so a model's stored ``tier``
maps to a band by score. Colours mirror the values currently hardcoded in ``helpers.js``
(RAG_COLORS, TIER_COLORS); Materiality/Complexity gain a seed colour ramp (they had none).
"""
from __future__ import annotations

from config.governance import (
    COMPLEXITY_ORDER,
    MATERIALITY_ORDER,
    RAG_MULTIPLIERS,
    RISK_HEATMAP_BY_TIER,
    TIER_LABELS,
    VALID_RAG_RATINGS,
)

# Mirrors src/static/js/helpers.js RAG_COLORS.
_RATING_COLOURS = {"Red": "#d32f2f", "Amber": "#f57c00", "Green": "#388e3c"}
# Mirrors src/static/js/helpers.js TIER_COLORS for tiers 1/2/3.
_MISSION_CRITICALITY_COLOURS = {1: "#d32f2f", 2: "#f57c00", 3: "#1976d2"}
# New — Materiality/Complexity carried no colour before; seed a low→high ramp.
_LEVEL_COLOURS = {"Low": "#66bb6a", "Medium": "#ffa726", "High": "#ef5350"}

# Ratings ordered most-severe first, matching helpers.js RAG_ORDER (Red<Amber<Green).
_RATING_ORDER = ("Red", "Amber", "Green")

_LEVEL_EXPLANATION = {
    "materiality": {
        "Low": "Limited financial or regulatory exposure if the model errs.",
        "Medium": "Material to a business line or a client portfolio.",
        "High": "Firm-wide financial, regulatory or reputational impact.",
    },
    "complexity": {
        "Low": "Transparent, well-understood method with few assumptions.",
        "Medium": "Several interacting components or calibrations.",
        "High": "Opaque or novel technique that is hard to validate.",
    },
}
_MISSION_CRITICALITY_EXPLANATION = {
    "Mission critical": "Directly drives P&L, capital or regulatory reporting.",
    "Important": "Feeds a key process but is not the primary driver.",
    "Not important": "Indicative or exploratory use only.",
}
_RATING_EXPLANATION = {
    "Red": "Unacceptable residual risk; escalate and remediate now.",
    "Amber": "Elevated risk; manage under an agreed remediation plan.",
    "Green": "Within appetite; routine monitoring.",
}


def _level_bands(order: tuple[str, ...], which: str) -> list[dict]:
    """Low/Medium/High-style bands for Materiality or Complexity, scored by position."""
    explain = _LEVEL_EXPLANATION[which]
    return [
        {"name": name, "colour": _LEVEL_COLOURS.get(name, "#9e9e9e"),
         "explanation": explain.get(name, ""), "score": i}
        for i, name in enumerate(order, start=1)
    ]


def _mission_criticality_bands() -> list[dict]:
    """Bands for Mission Criticality (was Tier). Score == the legacy tier integer."""
    return [
        {"name": TIER_LABELS[tier], "colour": _MISSION_CRITICALITY_COLOURS[tier],
         "explanation": _MISSION_CRITICALITY_EXPLANATION.get(TIER_LABELS[tier], ""),
         "score": tier}
        for tier in sorted(TIER_LABELS)
    ]


def _risk_rating_bands() -> list[dict]:
    """The overall risk ratings; score == the completeness escalation multiplier."""
    return [
        {"name": name, "colour": _RATING_COLOURS.get(name, "#9e9e9e"),
         "explanation": _RATING_EXPLANATION.get(name, ""), "score": RAG_MULTIPLIERS[name]}
        for name in _RATING_ORDER if name in VALID_RAG_RATINGS
    ]


def _default_grid() -> dict[str, dict[str, str]]:
    """One Materiality×Complexity grid per Mission-Criticality band, keyed by band name,
    reproducing ``RISK_HEATMAP_BY_TIER`` exactly. Cell key is ``"materiality|complexity"``."""
    return {
        TIER_LABELS[tier]: {f"{mat}|{comp}": rating
                            for (mat, comp), rating in RISK_HEATMAP_BY_TIER[tier].items()}
        for tier in sorted(TIER_LABELS)
    }


def default_policy() -> dict:
    """The seed risk policy — a fresh dict each call so callers can mutate safely."""
    return {
        "dimensions": {
            "mission_criticality": {"label": "Mission Criticality",
                                    "bands": _mission_criticality_bands()},
            "materiality": {"label": "Materiality",
                            "bands": _level_bands(MATERIALITY_ORDER, "materiality")},
            "complexity": {"label": "Complexity",
                           "bands": _level_bands(COMPLEXITY_ORDER, "complexity")},
        },
        "risk_ratings": _risk_rating_bands(),
        "grid": _default_grid(),
    }
