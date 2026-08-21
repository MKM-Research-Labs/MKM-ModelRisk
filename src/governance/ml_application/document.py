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
"""The ML Application Document: one PDF for a single ML Application.

The ML sibling of the Model Risk Document and the Product Document, and assembled
the same way -- generated from the record on request rather than stored, so it can
never be a stale copy of what the register actually says.
"""
from __future__ import annotations

from src.governance.latex import front_matter, history_page, logo_asset, preamble
from src.governance.ml_application._report import ml_application_section
from src.governance.model_inventory.review import compute_review_status
from src.governance.mrc import pack

DOC_TITLE = "ML Application Document"


def build_ml_application_document_tex(record: dict, settings: dict, as_of: str,
                                      *, logo: bool = False, issued_at: str = "") -> str:
    """LaTeX source for one ML Application's document.

    ``as_of`` is the date the record is read at (it decides whether a review is
    overdue); ``issued_at`` is when this copy was produced, shown on the title page
    so two documents issued the same day can still be told apart.
    """
    data = record.get("data", {})
    org = settings.get("fields", {}).get("org_name", "")
    title = str(record["ml_application_id"]) + " --- " + str(data.get("name") or "")
    review = compute_review_status(data.get("next_review_date"), as_of)
    return (
        preamble(DOC_TITLE, org_name=org) + "\\begin{document}\n"
        + front_matter(title, DOC_TITLE, org_name=org, date=issued_at or as_of,
                       logo=logo, toc=True)
        + history_page(issued_at or as_of,
                       DOC_TITLE + " generated from the ML Application register",
                       org_name=org)
        + ml_application_section(record, review)
        + "\\end{document}\n"
    )


def render_ml_application_document_pdf(record: dict, settings: dict, as_of: str,
                                       issued_at: str = "") -> bytes:
    """Build and compile one ML Application's document to PDF bytes."""
    assets = logo_asset(settings)
    tex = build_ml_application_document_tex(record, settings, as_of, logo=bool(assets),
                                            issued_at=issued_at)
    return pack.compile_tex(tex, assets)
