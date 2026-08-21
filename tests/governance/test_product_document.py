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
"""Tests for the Product Document (its LaTeX generation and PDF render)."""
from __future__ import annotations

import pytest

from src.governance.product.document import (
    build_product_document_tex, render_product_document_pdf)

SETTINGS = {"fields": {"org_name": "MKM"}}


@pytest.fixture
def resolve_models(monkeypatch):
    """Resolve MKM-EF-001 to a named model; anything else is unknown."""
    monkeypatch.setattr("src.governance.product._report_product.get_model",
                        lambda mid, config=None: {"model_id": mid, "data": {"name": "Event Frequency"}}
                        if mid == "MKM-EF-001" else None)


def _product(**data):
    base = {"product": "Government Bond", "identifier": "MKM-EF-001.QuantLib"}
    base.update(data)
    return {"product_id": "PRD-1", "data": base}


def test_document_leads_with_components_and_reports_the_record(resolve_models):
    product = _product(
        description="A rates product.",
        next_review_date="2020-01-01",   # in the past -> review is overdue
        components=[
            {"component_type": "Market Data Model", "model_id": "MKM-EF-001", "role": "hazard"},
            {"component_type": "Curve Model", "model_id": "MKM-GONE-001", "role": "curve"},
            {"component_type": "Other", "model_id": "", "role": "spare"},
        ],
        assumptions=[{"description": "Flat curve", "impact": "Low"}],
        operational_failure_events=[{"date": "2026-05-01", "description": "Feed outage",
                                     "responsible": ""}],
        documents=[{"category": "Monitoring", "filename": "m.pdf", "original_name": "m.pdf"}],
    )
    tex = build_product_document_tex(product, SETTINGS, "2026-08-03")
    assert "PRD-1 --- Government Bond" in tex          # title page
    assert "Components" in tex
    assert "MKM-EF-001 --- Event Frequency" in tex     # resolved component
    assert "not in the inventory" in tex               # MKM-GONE-001 is unknown
    assert "Derived identifier" in tex and "MKM-EF-001.QuantLib" in tex
    assert "Review due (at document date)" in tex
    assert "A rates product." in tex                   # description opens Overview
    assert "Feed outage" in tex                        # operational-event block
    assert "Attached documents" in tex and "m.pdf" in tex
    assert tex.strip().endswith("\\end{document}")


def test_document_states_absent_material_rather_than_omitting_it(resolve_models):
    # No description, no components, no registers, no attachments: every section is
    # present and marked as not recorded, so nothing is silently missing.
    tex = build_product_document_tex(_product(identifier=None), SETTINGS, "2026-08-03")
    assert "Components" in tex and "Not recorded" in tex
    assert "Not yet derived" in tex                    # identifier absent
    assert "Attached documents" in tex


def test_render_compiles_via_the_shared_engine(resolve_models, monkeypatch):
    captured = {}
    monkeypatch.setattr("src.governance.mrc.pack.compile_tex",
                        lambda tex, assets=None: (captured.update(tex=tex) or b"%PDF-prod"))
    out = render_product_document_pdf(_product(), SETTINGS, "2026-08-03", issued_at="2026-08-03 10:00 UTC")
    assert out == b"%PDF-prod"
    assert "Product Document" in captured["tex"]
    assert "2026-08-03 10:00 UTC" in captured["tex"]   # issued-at stamp on the title page
