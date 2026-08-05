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
"""Per-division, MRC-signed-off risk policy: seed parity + the sign-off lifecycle."""
from __future__ import annotations

import pytest

from config.governance import (
    COMPLEXITY_ORDER,
    MATERIALITY_ORDER,
    RAG_MULTIPLIERS,
    RISK_HEATMAP_BY_TIER,
    TIER_LABELS,
)
from src.governance.errors import DomainError
from src.governance.risk_policy import (
    approve_policy,
    default_policy,
    get_policy_draft,
    get_risk_policy,
    load,
    propose_policy,
    reject_policy,
)


def _edited_seed(colour="#000000"):
    """A valid variant of the seed (a colour change keeps the grid/rating names intact,
    so it still validates) — used to prove draft vs live behaviour."""
    policy = default_policy()
    policy["risk_ratings"][0]["colour"] = colour
    return policy


# --- Seed parity: the default reproduces today's hardcoded behaviour exactly ---

def test_seed_grid_matches_the_current_heatmap():
    grid = default_policy()["grid"]
    for tier, label in TIER_LABELS.items():
        expected = {f"{m}|{c}": rag for (m, c), rag in RISK_HEATMAP_BY_TIER[tier].items()}
        assert grid[label] == expected


def test_seed_rating_scores_are_the_completeness_multipliers():
    scores = {b["name"]: b["score"] for b in default_policy()["risk_ratings"]}
    assert scores == RAG_MULTIPLIERS


def test_seed_dimension_bands_match_the_current_vocabulary():
    dims = default_policy()["dimensions"]
    assert [b["name"] for b in dims["materiality"]["bands"]] == list(MATERIALITY_ORDER)
    assert [b["name"] for b in dims["complexity"]["bands"]] == list(COMPLEXITY_ORDER)
    assert [b["name"] for b in dims["mission_criticality"]["bands"]] == \
        [TIER_LABELS[t] for t in sorted(TIER_LABELS)]
    # Mission-Criticality band scores are the legacy tier integers.
    assert [b["score"] for b in dims["mission_criticality"]["bands"]] == sorted(TIER_LABELS)


def test_every_band_carries_the_full_quad():
    policy = default_policy()
    bands = [b for d in policy["dimensions"].values() for b in d["bands"]] + policy["risk_ratings"]
    for band in bands:
        assert {"name", "colour", "explanation", "score"} <= set(band)


# --- Baseline: a division that has never ratified runs on the seed ---

def test_division_with_no_policy_uses_the_seed():
    assert get_risk_policy("UntouchedDivision") == default_policy()
    assert load("UntouchedDivision")["state"] == "seed"


# --- Lifecycle: propose stays a draft until MRC approval ---

def test_proposed_policy_does_not_go_live_until_approved():
    div = "DivProposeOnly"
    propose_policy(division=div, policy=_edited_seed("#123456"), actor="admin")
    assert get_policy_draft(div) is not None
    assert get_risk_policy(div) == default_policy()          # live is still the seed
    assert load(div)["state"] == "draft"


def test_approval_makes_the_draft_live():
    div = "DivApprove"
    propose_policy(division=div, policy=_edited_seed("#abcdef"), actor="admin")
    approve_policy(division=div, actor="mrc", meeting_id="MTG-1")
    assert get_risk_policy(div)["risk_ratings"][0]["colour"] == "#abcdef"
    assert get_policy_draft(div) is None
    assert load(div)["state"] == "approved"


def test_divisions_are_isolated():
    propose_policy(division="DivA", policy=_edited_seed("#111111"), actor="a")
    approve_policy(division="DivA", actor="mrc")
    assert get_risk_policy("DivA")["risk_ratings"][0]["colour"] == "#111111"
    assert get_risk_policy("DivB") == default_policy()       # a different division is untouched


def test_rejection_leaves_the_live_policy_unchanged():
    div = "DivReject"
    propose_policy(division=div, policy=_edited_seed("#222222"), actor="a")
    reject_policy(division=div, actor="mrc")
    assert get_policy_draft(div) is None
    assert get_risk_policy(div) == default_policy()


def test_approve_requires_a_pending_draft():
    with pytest.raises(DomainError):
        approve_policy(division="NothingPending", actor="mrc")


# --- Validation guards the committee from a broken policy ---

def test_grid_referencing_an_unknown_rating_is_rejected():
    policy = default_policy()
    mc = next(iter(policy["grid"]))
    cell = next(iter(policy["grid"][mc]))
    policy["grid"][mc][cell] = "Nonexistent"
    with pytest.raises(DomainError):
        propose_policy(division="DivBadGrid", policy=policy, actor="a")


def test_missing_dimension_is_rejected():
    policy = default_policy()
    del policy["dimensions"]["complexity"]
    with pytest.raises(DomainError):
        propose_policy(division="DivBadDims", policy=policy, actor="a")
