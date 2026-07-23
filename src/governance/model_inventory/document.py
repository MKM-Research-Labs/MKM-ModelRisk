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
"""The Model Risk Document: one client-facing PDF for a single model.

The Model Risk Report covers the whole inventory in one pack, which is what a
committee wants but not what you hand to a client or an external validator asking
about one model. This is the same dossier -- classification, methodology,
governance, validation questions and evidence, assumptions, limitations,
weaknesses, remediation, dependencies, change history, MRC decisions and the
attached documents -- issued as a document in its own right, with the model on the
title page and its parts as top-level sections.

It is generated from the inventory on request rather than stored, so it can never
be a stale copy of the record it is supposed to describe.
"""
from __future__ import annotations

from src.governance.latex import front_matter, history_page, logo_asset, preamble
from src.governance.model_inventory._report_model import model_section
from src.governance.model_inventory.review import compute_review_status
from src.governance.mrc import pack

DOC_TITLE = "Model Risk Document"


def build_model_document_tex(model: dict, settings: dict, as_of: str,
                             *, logo: bool = False, issued_at: str = "") -> str:
    """LaTeX source for one model's Model Risk Document.

    ``as_of`` is the date the record is read at (it decides whether a review is
    overdue). ``issued_at`` is when this copy was produced, shown in full on the
    title page: two documents issued the same day describe different states of the
    inventory, so the date alone does not identify which one you are holding.
    """
    data = model.get("data", {})
    org = settings.get("fields", {}).get("org_name", "")
    title = str(model["model_id"]) + " --- " + str(data.get("name") or "")
    review = compute_review_status(data.get("next_review_date"), as_of)
    return (
        preamble(DOC_TITLE, org_name=org) + "\\begin{document}\n"
        + front_matter(title, DOC_TITLE, org_name=org, date=issued_at or as_of,
                       logo=logo, toc=True)
        + model_section(model, review, standalone=True)
        + "\\clearpage\n"
        + history_page(issued_at or as_of,
                       DOC_TITLE + " generated from the model inventory", org_name=org)
        + "\\end{document}\n"
    )


def render_model_document_pdf(model: dict, settings: dict, as_of: str,
                              issued_at: str = "") -> bytes:
    """Build and compile one model's Model Risk Document to PDF bytes."""
    assets = logo_asset(settings)
    tex = build_model_document_tex(model, settings, as_of, logo=bool(assets),
                                   issued_at=issued_at)
    return pack.compile_tex(tex, assets)
