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
"""Commands for a division's risk policy: propose a draft, MRC-approve it, or reject it.

Approval is what makes a policy live. It is expected to be driven from the division's
MRC meeting sign-off flow (like a model RAG sign-off), so ``approve_policy`` records the
meeting it was ratified at; until then a proposed policy sits as a draft and does not
affect any model's rating.
"""
from __future__ import annotations

from dataclasses import replace

from config.governance import AUDIT_POLICY_DEFAULTS
from src.database import Event, append_event
from src.governance.errors import DomainError
from src.governance.risk_policy._store import (
    AGGREGATE_TYPE,
    EVENT_POLICY_DOCUMENT,
    POLICY,
    load,
)

_DIMENSIONS = ("mission_criticality", "materiality", "complexity")
_BAND_KEYS = ("name", "colour", "explanation", "score")


def _validate_band(band, where: str) -> None:
    if not isinstance(band, dict):
        raise DomainError(f"{where}: each band must be an object")
    for key in _BAND_KEYS:
        if key not in band:
            raise DomainError(f"{where}: a band is missing '{key}'")
    if not str(band["name"]).strip():
        raise DomainError(f"{where}: a band has no name")


def _validate_audit(policy) -> None:
    """The audit section, if present, holds numbers and nothing else.

    Every key is optional — a division that has set two of them is audited on those
    two and the firm-wide values for the rest — but a key that is present and not a
    number would silently fall back at scoring time, which is the kind of quiet
    wrongness a governance figure must not have.
    """
    audit = policy.get("audit")
    if audit is None:
        return
    if not isinstance(audit, dict):
        raise DomainError("the audit section must be an object")
    for key, value in audit.items():
        if key not in AUDIT_POLICY_DEFAULTS:
            raise DomainError(f"unknown audit setting: {key}")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise DomainError(f"audit setting '{key}' must be a number")
        if value < 0:
            raise DomainError(f"audit setting '{key}' cannot be negative")
    acceptable = audit.get("acceptable_at", AUDIT_POLICY_DEFAULTS["acceptable_at"])
    conditional = audit.get("conditional_at", AUDIT_POLICY_DEFAULTS["conditional_at"])
    if conditional > acceptable:
        raise DomainError(
            "the conditional threshold cannot sit above the acceptable one: a record "
            "would be conditional and acceptable at the same score")


def _validate_policy(policy) -> None:
    """Structural validation. Bands carry the full {name,colour,explanation,score} quad;
    the grid covers exactly Mission-Criticality × Materiality × Complexity and only
    references defined risk ratings."""
    if not isinstance(policy, dict):
        raise DomainError("risk policy must be an object")
    _validate_audit(policy)
    dims = policy.get("dimensions")
    if not isinstance(dims, dict) or set(dims) != set(_DIMENSIONS):
        raise DomainError("risk policy needs dimensions: " + ", ".join(_DIMENSIONS))
    names: dict[str, list[str]] = {}
    for key in _DIMENSIONS:
        dim = dims[key]
        if not isinstance(dim, dict) or not str(dim.get("label", "")).strip():
            raise DomainError(f"dimension '{key}' needs a label")
        bands = dim.get("bands")
        if not isinstance(bands, list) or not bands:
            raise DomainError(f"dimension '{key}' needs at least one band")
        for band in bands:
            _validate_band(band, f"dimension '{key}'")
        band_names = [b["name"] for b in bands]
        if len(set(band_names)) != len(band_names):
            raise DomainError(f"dimension '{key}' has duplicate band names")
        names[key] = band_names

    ratings = policy.get("risk_ratings")
    if not isinstance(ratings, list) or not ratings:
        raise DomainError("risk policy needs at least one risk rating")
    for band in ratings:
        _validate_band(band, "risk ratings")
    rating_names = {b["name"] for b in ratings}
    if len(rating_names) != len(ratings):
        raise DomainError("risk ratings have duplicate names")

    grid = policy.get("grid")
    if not isinstance(grid, dict) or set(grid) != set(names["mission_criticality"]):
        raise DomainError("the grid must have one table per Mission-Criticality band")
    expected_cells = {f"{mat}|{comp}"
                      for mat in names["materiality"] for comp in names["complexity"]}
    for mc_name, cells in grid.items():
        if not isinstance(cells, dict) or set(cells) != expected_cells:
            raise DomainError(f"the '{mc_name}' table must cover every "
                              "Materiality × Complexity cell")
        for cell, rating in cells.items():
            if rating not in rating_names:
                raise DomainError(f"the '{mc_name}' table cell '{cell}' references an "
                                  f"unknown risk rating '{rating}'")


# The lifecycle is ``ratified_policy``; what belongs to a RISK policy is the
# validation above, which is why propose passes it in rather than the shared code
# knowing anything about bands, ratings or heatmap cells.
_POLICY = replace(POLICY, validate=_validate_policy)


def propose_policy(*, division: str, policy: dict, actor: str,
                   reason: str | None = None, config=None) -> Event:
    """Submit a division's draft risk policy for MRC sign-off. Validated now so a broken
    policy never reaches the committee; it stays a draft until approved."""
    return _POLICY.propose(scope=division, policy=policy, actor=actor,
                           reason=reason, config=config)


def approve_policy(*, division: str, actor: str, meeting_id: str | None = None,
                   reason: str | None = None, config=None) -> Event:
    """Ratify the division's pending draft — its MRC has signed it off, so it becomes the
    live policy. Records the meeting it was approved at for the audit trail."""
    return _POLICY.approve(scope=division, actor=actor, meeting_id=meeting_id,
                           reason=reason, config=config)


def reject_policy(*, division: str, actor: str, meeting_id: str | None = None,
                  reason: str | None = None, config=None) -> Event:
    """Decline/withdraw the division's pending draft. The live policy is unchanged."""
    return _POLICY.reject(scope=division, actor=actor, meeting_id=meeting_id,
                          reason=reason, config=config)


def set_policy_document(*, division: str, filename: str, original_name: str,
                        actor: str, reason: str | None = None, config=None) -> Event:
    """Attach the division's formal written policy document (the uploaded PDF/Word that
    the MRC ratifies), replacing any earlier one."""
    if not str(division).strip():
        raise DomainError("a risk policy document must belong to a division")
    state = load(division, config)
    return append_event(
        aggregate_type=AGGREGATE_TYPE, aggregate_id=division,
        event_type=EVENT_POLICY_DOCUMENT,
        payload={"filename": filename, "original_name": original_name},
        actor=actor, reason=reason, expected_version=state["version"], config=config,
    )
