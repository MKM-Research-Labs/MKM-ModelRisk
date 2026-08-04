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
"""The Product Document: one client-facing PDF for a single product.

The product-side twin of the Model Risk Document. It renders the product's own
record — the component models it pulls together, its classification, bindings,
governance, registers and MRC sign-off history — with the product on the title
page and its parts as top-level sections. It is generated from the product view on
request rather than stored, so it can never be a stale copy of the record.
"""
from __future__ import annotations

from src.governance.latex import front_matter, history_page, logo_asset, preamble
from src.governance.model_inventory.review import compute_review_status
from src.governance.mrc import pack
from src.governance.product._report_product import product_section

DOC_TITLE = "Product Document"


def build_product_document_tex(product: dict, settings: dict, as_of: str,
                               *, logo: bool = False, issued_at: str = "",
                               config=None) -> str:
    """LaTeX source for one product's Product Document.

    ``as_of`` is the date the record is read at (it decides whether a review is
    overdue); ``issued_at`` is when this copy was produced, shown on the title page
    so two documents issued the same day can still be told apart.
    """
    data = product.get("data", {})
    org = settings.get("fields", {}).get("org_name", "")
    title = str(product["product_id"]) + " --- " + str(data.get("product") or "")
    review = compute_review_status(data.get("next_review_date"), as_of)
    return (
        preamble(DOC_TITLE, org_name=org) + "\\begin{document}\n"
        + front_matter(title, DOC_TITLE, org_name=org, date=issued_at or as_of,
                       logo=logo, toc=True)
        + product_section(product, review, config=config)
        + "\\clearpage\n"
        + history_page(issued_at or as_of,
                       DOC_TITLE + " generated from the product register", org_name=org)
        + "\\end{document}\n"
    )


def render_product_document_pdf(product: dict, settings: dict, as_of: str,
                                issued_at: str = "", config=None) -> bytes:
    """Build and compile one product's Product Document to PDF bytes."""
    assets = logo_asset(settings)
    tex = build_product_document_tex(product, settings, as_of, logo=bool(assets),
                                     issued_at=issued_at, config=config)
    return pack.compile_tex(tex, assets)
