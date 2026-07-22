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
"""Tests for the per-model Model Risk Document."""
from __future__ import annotations

from src.governance.model_inventory.document import (build_model_document_tex,
                                                     render_model_document_pdf)

MODEL = {"model_id": "M1", "data": {
    "name": "Alpha", "tier": 2, "rag_rating": "Green",
    "description": "An alpha model.",
    "review_status": "Remediation", "next_review_date": "2020-01-01",
    "limitations": [{"description": "Thames only", "impact": "Medium"}],
}}

SETTINGS = {"fields": {"org_name": "MKM"}}


def test_document_is_about_one_model_and_names_it_on_the_title_page():
    tex = build_model_document_tex(MODEL, SETTINGS, "2026-06-22")
    assert "M1 --- Alpha" in tex
    assert "Model Risk Document" in tex
    assert tex.strip().endswith("\\end{document}")


def test_document_promotes_the_dossier_to_top_level_sections():
    """The model is the whole document, so its parts are sections in their own right
    rather than subsections of a heading the title page already carries."""
    tex = build_model_document_tex(MODEL, SETTINGS, "2026-06-22")
    for part in ("Classification", "Methodology", "Governance", "Limitations",
                 "Attached documents"):
        assert "\\section{" + part + "}" in tex
    assert "\\subsection{" not in tex


def test_document_separates_the_stored_review_status_from_the_derived_one():
    """``review_status`` tracks how far the validation review has got; the review-due
    status says whether the next review date has passed. Reporting one as the other
    would hide a real field behind a different question's answer."""
    tex = build_model_document_tex(MODEL, SETTINGS, "2026-06-22")
    assert "Remediation" in tex                       # the stored workflow status
    assert "Review due (at report date)" in tex
    assert "Overdue" in tex                           # derived from the 2020 date


def test_render_model_document_pdf(monkeypatch):
    monkeypatch.setattr("src.governance.mrc.pack.compile_tex",
                        lambda tex, assets=None: b"%PDF-stub")
    assert render_model_document_pdf(MODEL, {"fields": {}}, "2026-06-22") == b"%PDF-stub"
