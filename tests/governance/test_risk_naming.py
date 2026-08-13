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
"""A division renames a risk dimension, and everything follows.

The three dimensions are structural; what they are called is the division's. The
moment a name is written into a field spec, a report heading or a paragraph of
prose, that surface keeps printing the old word after a rename — precisely when the
new one matters. These tests hold the rule: ask the policy, never spell it out.
"""
from __future__ import annotations

from src.governance.risk_policy.document import build_policy_document_tex
from src.governance.risk_policy.naming import dimension_label, field_label

_RENAMED = {
    "dimensions": {
        "mission_criticality": {"label": "Business Impact",
                                "bands": [{"name": "Critical", "score": 1, "colour": "#d32f2f"}]},
        "materiality": {"label": "Materiality",
                        "bands": [{"name": "High", "score": 3, "colour": "#d32f2f"}]},
        "complexity": {"label": "Problematic",
                       "bands": [{"name": "High", "score": 3, "colour": "#d32f2f"}]},
    },
    "risk_ratings": [{"name": "Stop", "score": 2, "colour": "#d32f2f"}],
    "grid": {"Critical": {"High|High": "Stop"}},
}


def test_a_dimension_is_called_what_the_division_calls_it():
    assert dimension_label("complexity", policy=_RENAMED) == "Problematic"
    assert dimension_label("mission_criticality", policy=_RENAMED) == "Business Impact"


def test_a_dimension_with_no_policy_falls_back_to_its_own_key():
    """Derived from the structure, not from a name somebody typed into the source."""
    assert dimension_label("mission_criticality", policy={}) == "Mission criticality"


def test_a_record_field_takes_the_dimension_name_and_so_does_its_rationale():
    """Renaming a dimension renames the field that justifies it too — otherwise the
    justification is left labelled after a dimension that no longer exists."""
    assert field_label("complexity", "Complexity", policy=_RENAMED) == "Problematic"
    assert field_label("tier", "Tier", policy=_RENAMED) == "Business Impact"
    assert field_label("complexity_rationale", "Complexity rationale",
                       policy=_RENAMED) == "Problematic rationale"


def test_an_ordinary_field_keeps_its_own_label():
    assert field_label("owner", "Owner", policy=_RENAMED) == "Owner"


def test_the_policy_document_prints_the_divisions_own_names():
    """The document reports on the very policy that renamed them, so printing the
    platform's default names would misdescribe its own subject."""
    tex = build_policy_document_tex(
        "PhysicalRisk", {"live": _RENAMED, "state": "approved"},
        {"fields": {"org_name": "Sterling Bank"}})
    assert "Problematic" in tex and "Business Impact" in tex
    assert "Complexity" not in tex
    assert "Mission-Criticality" not in tex and "Mission Criticality" not in tex
