# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Composite model risk rating (pure).

Synthesises a model's read-model document into a weighted score and an overall
rating, mirroring the PhysicalRisk breakdown: validation coverage, remediation
health, review currency, assumption risk and limitation risk.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from config.governance import (
    EVENTS_WINDOW_DAYS,
    RISK_ACCEPTABLE_AT,
    RISK_CONDITIONAL_AT,
    RISK_HEATMAP,
    RISK_WEIGHTS,
)


def _validation_coverage(data: dict[str, Any]) -> float:
    questions = data.get("validation_questions", [])
    if not questions:
        return 0.0
    scored = 0.0
    for question in questions:
        if question.get("status") == "Addressed":
            scored += 1.0
        elif question.get("status") == "Partially Addressed":
            scored += 0.5
    return scored / len(questions)


def _remediation_health(data: dict[str, Any]) -> float:
    items = data.get("remediation_steps", [])
    if not items:
        return 1.0
    closed = sum(1 for item in items if item.get("status") == "Closed")
    return closed / len(items)


def _review_currency(data: dict[str, Any], as_of: str) -> float:
    next_review = data.get("next_review_date")
    if not next_review:
        return 0.0
    return 1.0 if next_review >= as_of else 0.0


def _impact_health(items: list) -> float:
    if not items:
        return 1.0
    high = sum(1 for item in items if item.get("impact") == "High")
    return 1.0 - high / len(items)


def _heatmap_rag(materiality: str | None, complexity: str | None) -> str | None:
    """3×3 heatmap lookup: the owner-set Materiality × Complexity cell → RAG."""
    if not materiality or not complexity:
        return None
    return RISK_HEATMAP.get((materiality, complexity))


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
    """Return the risk rating envelope: heatmap headline, composite breakdown
    and past-year events count.

    ``rating`` and ``score`` remain the composite view for callers (the Model
    Risk Report PDF, PVM headers, list badges) — the heatmap is additional
    context surfaced primarily on the Risk Rating tab.
    """
    scores = {
        "validation_coverage": _validation_coverage(data),
        "remediation_health": _remediation_health(data),
        "review_currency": _review_currency(data, as_of),
        "assumption_risk": _impact_health(data.get("assumptions", [])),
        "limitation_risk": _impact_health(data.get("limitations", [])),
    }
    composite = sum(scores[key] * weight for key, _label, weight in RISK_WEIGHTS)
    if composite >= RISK_ACCEPTABLE_AT:
        rating = "Acceptable"
    elif composite >= RISK_CONDITIONAL_AT:
        rating = "Conditional"
    else:
        rating = "Unacceptable"
    components = [
        {"key": key, "label": label, "weight": weight, "score": scores[key]}
        for key, label, weight in RISK_WEIGHTS
    ]
    materiality = data.get("materiality")
    complexity = data.get("complexity")
    heatmap = {
        "materiality": materiality,
        "complexity": complexity,
        "rag": _heatmap_rag(materiality, complexity),
        # Full lookup as pipe-joined keys so the UI can colour every cell
        # without knowing the mapping itself (R1: config is the single truth).
        "grid": {f"{m}|{c}": rag for (m, c), rag in RISK_HEATMAP.items()},
    }
    return {
        "rating": rating,
        "score": round(composite, 4),
        "components": components,
        "heatmap": heatmap,
        "approved_rag": data.get("rag_rating"),
        "events_in_window": _events_in_window(data, as_of),
        "events_window_days": EVENTS_WINDOW_DAYS,
    }
