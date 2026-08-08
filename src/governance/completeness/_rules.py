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
"""Gap detection and severity scoring for the completeness audit.

No I/O happens here, so every rule is trivially unit-testable and the arithmetic
an auditor is asked to trust can be checked in isolation from the report that
prints it. The weights themselves live in ``config.governance`` (rule R1); this
module only applies them.

Each gap carries its own factors rather than only the product, so a finding can
be defended line by line: the register prints "0.90 x 1.00 x 1.25 x 1.15 x 1.10
= 1.42, Critical", not an unexplained 1.42.
"""
from __future__ import annotations

from datetime import date
from typing import Any

from config.governance import (
    AUDIT_POLICY_DEFAULTS,
    COLLECTION_CRITICALITY,
    DEFAULT_COLLECTION_CRITICALITY,
    DEFAULT_DOC_CRITICALITY,
    DEFAULT_FIELD_CRITICALITY,
    DOC_CRITICALITY,
    EVENT_PRESSURE_CAP,
    EVENT_PRESSURE_PER_EVENT,
    EXEMPT_COLLECTIONS,
    EXEMPT_FIELDS,
    FIELD_CRITICALITY,
    RAG_MULTIPLIERS,
    REMEDIATION_ACTIONS,
    REMEDIATION_SLA_DAYS,
    SEVERITY_BANDS,
    STALENESS_NONE,
    STALENESS_STEPS,
    TIER_WEIGHTS,
    UNRATED_MULTIPLIER,
    UNTIERED_WEIGHT,
)
from config.governance import DOC_CATEGORY_SATISFIED_BY, EXEMPT_DOC_CATEGORIES
from src.governance.completeness._gaps import (
    _collection_gaps,
    _collection_shortfall,
    _document_gaps,
    _entries,
    _field_gaps,
    _held_categories,
    _recorded,
)


# ---------------------------------------------------------------------------
# Escalation factors
# ---------------------------------------------------------------------------

def _setting(policy: dict | None, key: str) -> float:
    """One audit setting: the division's if its committee has ratified one, else the
    firm-wide value. Read here rather than at the call sites so a division that has
    set two of seven is scored on those two and the defaults for the rest."""
    value = (policy or {}).get(key)
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) \
        else AUDIT_POLICY_DEFAULTS[key]


def tier_weight(tier: Any, policy: dict | None = None) -> float:
    """The tier's share of the severity. An untiered record escalates rather
    than damps: the missing tier is itself the reason it needs looking at."""
    try:
        return TIER_WEIGHTS[int(tier)]
    except (TypeError, ValueError, KeyError):
        return _setting(policy, "untiered_weight")


def rag_multiplier(rag: Any, scores: dict | None = None,
                   policy: dict | None = None) -> float:
    """Escalation from the governed risk rating; unrated sits above the lowest rating.

    ``scores`` is the division policy's rating→score map (carried on the risk envelope);
    when absent it falls back to the firm-wide defaults, so the seed reproduces today's
    Red/Amber/Green = 1.25/1.10/1.00."""
    table = scores if scores is not None else RAG_MULTIPLIERS
    return table.get(str(rag), _setting(policy, "unrated_multiplier"))


def event_pressure(events: int, policy: dict | None = None) -> float:
    """Escalation from operational failures in the rolling window, capped so a
    single bad year cannot dominate the whole ranking."""
    count = max(0, int(events or 0))
    return min(1.0 + count * _setting(policy, "event_pressure_per_event"),
               _setting(policy, "event_pressure_cap"))


def staleness(next_review_date: Any, as_of: str) -> float:
    """Escalation from how far past its next review the record has run.

    A record not yet due, or with no review scheduled, is not escalated here: an
    absent ``next_review_date`` is already raised as its own gap, and charging
    for it twice would double-count the same omission.
    """
    if not next_review_date:
        return STALENESS_NONE
    try:
        due = date.fromisoformat(str(next_review_date))
        today = date.fromisoformat(str(as_of))
    except ValueError:
        return STALENESS_NONE
    overdue = (today - due).days
    if overdue < 0:
        return STALENESS_NONE
    for threshold, multiplier in STALENESS_STEPS:
        if overdue >= threshold:
            return multiplier
    return STALENESS_NONE


def band(severity: float) -> str:
    """The severity band a score falls in. Ordered worst first; first match wins."""
    for label, floor in SEVERITY_BANDS:
        if severity >= floor:
            return label
    return SEVERITY_BANDS[-1][0]


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------

def _action(gap: dict, entity_kind: str) -> str:
    """The instruction attached to a finding, so it can be handed to an owner."""
    template_key = gap["kind"]
    if gap.get("partial"):
        template_key = "collection_partial"
    # Labels keep the case they were authored with. Lower-casing them reads more
    # naturally mid-sentence for most fields but mangles the acronyms -- "record
    # rag rating", "record mrc sign-off" -- and an instruction an owner has to
    # decode is worse than one with a capital in the middle of it.
    return REMEDIATION_ACTIONS[template_key].format(
        item=gap["label"], entity=entity_kind.lower(),
        detail=gap.get("detail", ""))


def audit_entity(
    *, entity_kind: str, entity_id: str, entity_name: str, data: dict,
    field_specs: dict, collection_specs: dict, doc_categories: tuple,
    risk: dict, as_of: str, available=None,
) -> dict:
    """Score every gap on one model or product.

    ``risk`` is the envelope from ``compute_risk_rating``, so the audit escalates
    on exactly the rating and event count the Risk Rating tab shows rather than
    computing a second opinion of its own.
    """
    tier = data.get("tier")
    rag = risk.get("heatmap", {}).get("rag") or data.get("rag_rating")
    audit_policy = risk.get("audit_policy")
    factors = {
        "tier_weight": tier_weight(tier, audit_policy),
        # The rating's escalation weight is its score in the division's policy (carried on
        # the risk envelope); an unrated model sits just above the lowest rating.
        "rag_multiplier": rag_multiplier(rag, risk.get("rag_scores"), audit_policy),
        "event_pressure": event_pressure(risk.get("events_in_window", 0), audit_policy),
        "staleness": staleness(data.get("next_review_date"), as_of),
    }
    escalation = (factors["tier_weight"] * factors["rag_multiplier"]
                  * factors["event_pressure"] * factors["staleness"])

    raw = (_field_gaps(data, field_specs)
           + _collection_gaps(data, collection_specs)
           + _document_gaps(data, doc_categories, available))

    gaps = []
    for gap in raw:
        severity = gap["criticality"] * escalation
        label = band(severity)
        gaps.append({
            **gap, **factors,
            "entity_kind": entity_kind, "entity_id": entity_id,
            "entity_name": entity_name, "tier": tier, "rag": rag,
            "criticality": round(gap["criticality"], 4),
            "severity": round(severity, 4), "band": label,
            "sla_days": REMEDIATION_SLA_DAYS[label],
            "action": _action(gap, entity_kind),
        })
    gaps.sort(key=lambda g: (-g["severity"], g["kind"], g["key"]))

    # Weighted completeness: how much of the criticality this record was asked to
    # carry it actually holds. Unweighted percentages flatter a record that has
    # filled in its cheap fields and left the expensive ones blank.
    missing = sum(g["criticality"] for g in gaps)
    total = missing + _carried(data, field_specs, collection_specs,
                               doc_categories, available)
    return {
        "entity_kind": entity_kind, "entity_id": entity_id,
        "entity_name": entity_name, "tier": tier, "rag": rag,
        "events_in_window": risk.get("events_in_window", 0),
        "escalation": round(escalation, 4), **factors,
        "completeness": round(1 - missing / total, 4) if total else 1.0,
        # The thresholds this record was scored against, carried on the row. Records
        # from different divisions sit in one report, so "is this one acceptable?"
        # cannot be answered by one number read from config at printing time.
        "acceptable_at": _setting(audit_policy, "acceptable_at"),
        "conditional_at": _setting(audit_policy, "conditional_at"),
        "gaps": gaps,
    }


def _carried(data: dict, field_specs: dict, collection_specs: dict,
             doc_categories: tuple, available=None) -> float:
    """Total criticality of everything this record does hold — the denominator
    of the completeness ratio."""
    total = sum(FIELD_CRITICALITY.get(k, DEFAULT_FIELD_CRITICALITY)
                for k in field_specs
                if k not in EXEMPT_FIELDS and _recorded(data.get(k)))
    for name in collection_specs:
        if name in EXEMPT_COLLECTIONS:
            continue
        answered, expected = _collection_shortfall(data, name)
        total += (COLLECTION_CRITICALITY.get(name, DEFAULT_COLLECTION_CRITICALITY)
                  * min(answered / expected, 1.0) if expected else 0)
    # Documentation counts toward completeness on exactly the terms it is asked
    # for: a category never demanded (History) is not credited either, and one
    # closed by a broader pack is credited through that pack. Crediting a
    # category the register does not require would let a record climb above the
    # threshold on evidence nobody asked it to produce.
    retrievable, _ = _held_categories(data, available)
    for category in doc_categories:
        if category in EXEMPT_DOC_CATEGORIES:
            continue
        covering = DOC_CATEGORY_SATISFIED_BY.get(category)
        if category in retrievable or (covering and covering in retrievable):
            total += DOC_CRITICALITY.get(category, DEFAULT_DOC_CRITICALITY)
    return total
