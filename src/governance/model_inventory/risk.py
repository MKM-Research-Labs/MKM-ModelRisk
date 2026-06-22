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

from typing import Any

from config.governance import RISK_ACCEPTABLE_AT, RISK_CONDITIONAL_AT, RISK_WEIGHTS


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


def compute_risk_rating(data: dict[str, Any], *, as_of: str) -> dict[str, Any]:
    """Return ``{rating, score, components:[{key,label,weight,score}]}``."""
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
    return {"rating": rating, "score": round(composite, 4), "components": components}
