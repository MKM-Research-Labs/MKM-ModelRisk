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
"""What the completeness audit scores a division against is the division's to set.

The thresholds and escalation factors decide every completeness figure and every
remediation deadline in the estate — the thing a regulator asks to see the basis
for. They belong on the division's risk policy, ratified by the committee that
already ratifies the categorisation, rather than in the platform's source.

Everything here is optional: a division that has ratified none of it is scored on
the firm-wide values, exactly as it was before the section existed.
"""
from __future__ import annotations

import pytest

from config.governance import AUDIT_POLICY_DEFAULTS
from config.governance._completeness_weights import AUDIT_WEIGHT_KEYS
from src.governance.completeness._rules import (event_pressure, rag_multiplier,
                                                tier_weight)
from src.governance.errors import DomainError
from src.governance.risk_policy import default_policy
from src.governance.risk_policy.commands import _validate_policy


def test_the_seed_reproduces_the_firm_wide_values():
    """A fresh division is audited exactly as it was before the section existed:
    the firm-wide settings, and criticality-weight sections left empty so every
    weight reads through to the firm-wide tables."""
    assert default_policy()["audit"] == {
        **AUDIT_POLICY_DEFAULTS, **{key: {} for key in AUDIT_WEIGHT_KEYS}}


def test_a_division_can_set_what_it_is_scored_against():
    policy = {"untiered_weight": 0.5, "event_pressure_per_event": 0.2,
              "event_pressure_cap": 2.0, "unrated_multiplier": 1.5}
    assert tier_weight(None, policy) == 0.5
    assert tier_weight(1, policy) == 1.0, "a tiered record still weights by its tier"
    assert event_pressure(3, policy) == pytest.approx(1.6)
    assert event_pressure(20, policy) == 2.0, "still capped, at the division's cap"
    assert rag_multiplier("Unrated", None, policy) == 1.5


def test_settings_it_has_not_ratified_fall_back_one_at_a_time():
    """A division that has set two of seven is scored on those two and the
    firm-wide values for the rest — not all-or-nothing."""
    policy = {"untiered_weight": 0.5}
    assert tier_weight(None, policy) == 0.5
    assert event_pressure(3, policy) == pytest.approx(1.15)


def test_a_setting_that_is_not_a_number_is_refused_at_the_gate():
    """Refused when the policy is proposed, not silently ignored at scoring time:
    a governance figure must not quietly rest on a value nobody meant."""
    policy = default_policy()
    policy["audit"]["acceptable_at"] = "high"
    with pytest.raises(DomainError, match="must be a number"):
        _validate_policy(policy)


def test_an_unknown_setting_is_refused():
    policy = default_policy()
    policy["audit"]["fudge_factor"] = 2
    with pytest.raises(DomainError, match="unknown audit setting"):
        _validate_policy(policy)


def test_the_conditional_threshold_cannot_sit_above_the_acceptable_one():
    """It would make a record conditional and acceptable at the same score."""
    policy = default_policy()
    policy["audit"]["conditional_at"] = 0.95
    with pytest.raises(DomainError, match="conditional threshold"):
        _validate_policy(policy)


def test_a_policy_with_no_audit_section_is_still_valid():
    """Every division's policy predates this section; none of them is now invalid."""
    policy = default_policy()
    del policy["audit"]
    _validate_policy(policy)
