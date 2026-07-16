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
"""Tests for the Model Risk Report generation."""
from __future__ import annotations

from src.governance.model_inventory.report import build_report_tex, render_report_pdf

MODELS = [
    {"model_id": "M1", "data": {"name": "Alpha", "tier": 2, "rag_rating": "Green",
                                "next_review_date": "2030-01-01",
                                "validation_questions": [{"status": "Addressed"}]}},
    {"model_id": "M2", "data": {"name": "Beta", "tier": 1, "rag_rating": "Amber",
                                "validation_questions": []}},
]


def test_build_report_tex_has_models_and_summary():
    tex = build_report_tex(MODELS, {"fields": {"org_name": "MKM"}}, "2026-06-22")
    assert "Model Risk Report" in tex
    assert "M1" in tex and "Alpha" in tex and "M2" in tex
    assert "Models: 2" in tex and "MKM" in tex
    assert tex.strip().endswith("\\end{document}")


def test_render_report_pdf(monkeypatch):
    monkeypatch.setattr("src.governance.mrc.pack.compile_tex", lambda tex, assets=None: b"%PDF-stub")
    assert render_report_pdf(MODELS, {"fields": {}}, "2026-06-22") == b"%PDF-stub"
