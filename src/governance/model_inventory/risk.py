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

from config.governance import EVENTS_WINDOW_DAYS
from src.governance.risk_policy import load as _load_policy


def _mission_criticality_band(policy: dict, tier: Any) -> dict:
    """The Mission-Criticality band a model's ``tier`` selects, from the division's
    policy. A band's score is its tier value, so we match by score; an out-of-range
    tier clamps to the nearest band and a missing/unparseable one is the most
    conservative (lowest-score) band — mirroring the legacy 1-3 clamp."""
    bands = policy["dimensions"]["mission_criticality"]["bands"]
    by_score = {band["score"]: band for band in bands}
    try:
        wanted = int(tier)
    except (TypeError, ValueError):
        return by_score[min(by_score)]
    if wanted in by_score:
        return by_score[wanted]
    return by_score[min(max(wanted, min(by_score)), max(by_score))]


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


def compute_risk_rating(data: dict[str, Any], *, as_of: str, config=None) -> dict[str, Any]:
    """Return the risk rating envelope: the heatmap cell, the owner's recorded
    rating, whether the MRC has signed that cell off, and the events count.

    The heatmap is resolved from the model's DIVISION policy (the live, MRC-approved
    one, or the firm-wide seed for a division that has not set its own), so different
    divisions can carry different risk vocabularies and grids."""
    materiality = data.get("materiality")
    complexity = data.get("complexity")
    tier = data.get("tier")
    policy_state = _load_policy(data.get("division") or "", config)
    policy = policy_state["live"]
    approved_at = policy_state.get("approved_at")
    band = _mission_criticality_band(policy, tier)
    table = policy["grid"].get(band["name"], {})
    heatmap = {
        "tier": tier,
        "tier_band": band["score"],
        "tier_label": band["name"],
        "materiality": materiality,
        "complexity": complexity,
        # The owner-set Materiality × Complexity cell → risk rating (only when both axes set).
        "rag": table.get(f"{materiality}|{complexity}") if materiality and complexity else None,
        # The band's full lookup as pipe-joined keys so the UI can colour every cell
        # without knowing the mapping itself (the policy is the single truth).
        "grid": dict(table),
        # The dimension band names in policy order, so the UI draws the axes from the
        # division's own vocabulary rather than hardcoded Low/Medium/High literals.
        "axes": {
            "materiality": [b["name"] for b in policy["dimensions"]["materiality"]["bands"]],
            "complexity": [b["name"] for b in policy["dimensions"]["complexity"]["bands"]],
        },
        # Each rating's colour, so the UI shades every cell from the division policy
        # instead of a hardcoded RAG palette.
        "rating_colours": {r["name"]: r["colour"] for r in policy["risk_ratings"]},
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
    live_signoff = bool(
        latest_signoff and latest_signoff.get("outcome") not in ("Rejected", "Revoked"))
    signed_off = bool(
        heatmap["rag"] and live_signoff
        and latest_signoff.get("to_rating") == heatmap["rag"]
    )
    # A sign-off recorded before the division's current categorisation was approved was
    # made under older categories: the model must be re-classified by its owner and
    # re-sent to the MRC. Such a model is not treated as signed off.
    signoff_date = (latest_signoff or {}).get("date")
    needs_reclassification = bool(
        live_signoff and approved_at and signoff_date and signoff_date < approved_at)
    if needs_reclassification:
        signed_off = False
    return {
        "heatmap": heatmap,
        "approved_rag": data.get("rag_rating"),
        "signed_off": signed_off,
        # True when a prior sign-off is stale because the categorisation has since changed.
        "needs_reclassification": needs_reclassification,
        "events_in_window": _events_in_window(data, as_of),
        "events_window_days": EVENTS_WINDOW_DAYS,
        "signoff_history": signoff_history,
        # Each risk rating's numeric score, from the division's policy. The completeness
        # audit escalates on this, so a division's own multipliers drive its remediation.
        "rag_scores": {rating["name"]: rating["score"]
                       for rating in policy.get("risk_ratings", [])},
    }
