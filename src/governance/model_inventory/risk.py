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
"""A model's risk rating: the tier heatmap, plus what the committee has done (pure).

The rating is the cell the model occupies on its tier's Materiality x Complexity
heatmap, together with the rating the owner has recorded, whether the MRC has
signed that cell off, and how many operational failures fall in the rolling
window.

There is deliberately no second, derived score here. One rating the committee
sets and reviews is the model's risk statement; a parallel composite invited a
reader to ask which of the two numbers was the real one.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from config.governance import (
    EVENTS_WINDOW_DAYS,
    RISK_HEATMAP_BY_TIER,
    RISK_TIER_LABELS,
)


def _tier_band(tier: Any) -> int:
    """Map a model tier to its heatmap band (1/2/3).

    Tiers are 1-3; the clamp is a safety net for any out-of-range legacy value,
    and anything missing or unparseable is treated as Tier 1 (most conservative)."""
    try:
        return min(max(int(tier), 1), 3)
    except (TypeError, ValueError):
        return 1


def _heatmap_rag(tier: Any, materiality: str | None, complexity: str | None) -> str | None:
    """Heatmap lookup: the owner-set Materiality × Complexity cell for the
    model's tier band → RAG."""
    if not materiality or not complexity:
        return None
    return RISK_HEATMAP_BY_TIER[_tier_band(tier)].get((materiality, complexity))


def _events_in_window(data: dict[str, Any], as_of: str) -> int:
    """Count operational failure events whose date falls within the rolling window."""
    events = data.get("operational_failure_events") or []
    if not events:
        return 0
    try:
        as_of_date = date.fromisoformat(as_of)
    except ValueError:
        return 0
    cutoff = as_of_date - timedelta(days=EVENTS_WINDOW_DAYS)
    count = 0
    for event in events:
        event_date = event.get("date")
        if not event_date:
            continue
        try:
            parsed = date.fromisoformat(event_date)
        except ValueError:
            continue
        if cutoff <= parsed <= as_of_date:
            count += 1
    return count


def compute_risk_rating(data: dict[str, Any], *, as_of: str) -> dict[str, Any]:
    """Return the risk rating envelope: the heatmap cell, the owner's recorded
    rating, whether the MRC has signed that cell off, and the events count."""
    materiality = data.get("materiality")
    complexity = data.get("complexity")
    tier = data.get("tier")
    band = _tier_band(tier)
    table = RISK_HEATMAP_BY_TIER[band]
    heatmap = {
        "tier": tier,
        "tier_band": band,
        "tier_label": RISK_TIER_LABELS[band],
        "materiality": materiality,
        "complexity": complexity,
        "rag": _heatmap_rag(tier, materiality, complexity),
        # The tier's full lookup as pipe-joined keys so the UI can colour every
        # cell without knowing the mapping itself (R1: config is the single truth).
        "grid": {f"{m}|{c}": rag for (m, c), rag in table.items()},
    }
    # A rating is "signed off" only once the MRC has approved the current heatmap
    # RAG — i.e. the most recent sign-off recorded that exact rating. This holds
    # even when the owner and heatmap already agree: agreement is not approval, so
    # a never-signed-off model (or one whose heatmap has since moved) still needs
    # MRC sign-off.
    # A rejected or revoked latest entry un-does the sign-off even if it names the
    # current rating: the standing state is the outcome of the *most recent*
    # decision, so a Revoke returns the subject to "needs MRC sign-off".
    signoff_history = data.get("signoff_history") or []
    latest_signoff = signoff_history[-1] if signoff_history else None
    signed_off = bool(
        heatmap["rag"] and latest_signoff
        and latest_signoff.get("outcome") not in ("Rejected", "Revoked")
        and latest_signoff.get("to_rating") == heatmap["rag"]
    )
    return {
        "heatmap": heatmap,
        "approved_rag": data.get("rag_rating"),
        "signed_off": signed_off,
        "events_in_window": _events_in_window(data, as_of),
        "events_window_days": EVENTS_WINDOW_DAYS,
        "signoff_history": signoff_history,
    }
