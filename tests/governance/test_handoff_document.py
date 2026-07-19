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
"""The Model Interoperability Validation document (LaTeX source, no compiler).

Exercises ``build_handover_tex`` — the pure LaTeX builder — so the document's
structure and its data-driven sections are checked without needing tectonic.
"""
from __future__ import annotations

from src.governance.model_handoff.document import build_handover_tex

AS_OF = "2026-07-19"


def _handoff(**data):
    base = {"from_model": "A", "to_model": "B", "status": "Draft", "field_lineage": []}
    base.update(data)
    return {"handoff_id": "A~B", "data": base}


def test_document_has_title_and_endpoints():
    tex = build_handover_tex(_handoff(), None, None, AS_OF)
    assert "Model Interoperability Validation" in tex
    assert "A $\\rightarrow$ B" in tex


def test_all_template_sections_are_present():
    tex = build_handover_tex(_handoff(), None, None, AS_OF)
    for section in ("Executive Summary of the Handover", "Provider--Consumer Specifics",
                    "Scope of Handover", "Handover Parameters (Field Lineage)",
                    "History", "Handover Controls and Usage", "Distribution Comparison",
                    "Stress Testing", "Limitations and Caveats", "Model Risk Assessment",
                    "Sign-offs"):
        assert section in tex


def test_field_lineage_pair_is_rendered():
    h = _handoff(field_lineage=[{
        "provider_field": "spread", "provider_type": "float", "provider_units": "bps",
        "consumer_field": "spread_in", "consumer_type": "float", "note": "direct map",
    }])
    tex = build_handover_tex(h, None, None, AS_OF)
    assert "spread" in tex and "direct map" in tex


def test_empty_field_lineage_shows_a_placeholder():
    tex = build_handover_tex(_handoff(), None, None, AS_OF)
    assert "No field mappings declared yet" in tex


def test_provider_and_consumer_model_details_appear():
    provider = {"data": {"name": "Storm-Gauge", "owner": "bob", "tier": 2}}
    consumer = {"data": {"name": "PRS Pricing", "owner": "carol", "tier": 2}}
    tex = build_handover_tex(_handoff(), provider, consumer, AS_OF)
    assert "Storm-Gauge" in tex and "PRS Pricing" in tex


def test_approved_handoff_states_the_mrc_signoff():
    h = _handoff(status="Approved", mrc_signoff_meeting="MTG1", mrc_signoff_date="2026-06-30")
    tex = build_handover_tex(h, None, None, AS_OF)
    assert "Approved by the MRC at MTG1" in tex and "2026-06-30" in tex


def test_scope_includes_the_compatibility_note():
    tex = build_handover_tex(_handoff(compatibility="units aligned throughout"), None, None, AS_OF)
    assert "units aligned throughout" in tex
