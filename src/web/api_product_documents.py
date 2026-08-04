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
"""Generated outputs for a product: its Product Document and its full pack.

The product-side twin of ``api_model_documents``. These endpoints produce a file
rather than read or write the register, and each is built on request so it can
never be a stale copy of the record. They attach to ``product_bp`` to keep the
``/api/products`` URL space in one place.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from flask import Response, jsonify

from config.governance import HISTORY_DOC_CATEGORY
from src.governance.documents import add_document, product_scope
from src.governance.mrc.pack import TectonicNotFound
from src.governance.product import get_product, rebuild_product_view
from src.governance.product.commands import AGGREGATE_TYPE as PRODUCT_AGGREGATE
from src.governance.product.document import render_product_document_pdf
from src.governance.product.pack import PACK_NAME, build_product_pack, pack_manifest
from src.governance.mrc_settings import get_settings
from src.web._helpers import request_actor
from src.web.api_product import product_bp


def _attachment(name: str) -> str:
    return 'attachment; filename="' + name + '"'


def _file_history_copy(product_id: str, pdf: bytes, stamp: str, issued_at: str) -> None:
    """File the issued Product Document against the product under History, so every
    issued version is kept — the copy records what the product looked like when the
    document went out (the transaction-time axis, as for a model's document)."""
    name = f"{product_id}_product_document_{stamp}.pdf"
    add_document(aggregate_type=PRODUCT_AGGREGATE, aggregate_id=product_id,
                 scope=product_scope(product_id), category=HISTORY_DOC_CATEGORY,
                 filename=name, data=pdf,
                 description="Product Document issued " + issued_at,
                 actor=request_actor())
    rebuild_product_view()


@product_bp.get("/<product_id>/document.pdf")
def product_document(product_id: str):
    """One product's Product Document, generated on request and filed under History
    so every issued version is kept."""
    product = get_product(product_id)
    if product is None:
        return jsonify({"error": "product not found"}), 404
    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y-%m-%dT%H%M%S.%f")[:-3] + "Z"
    issued_at = now.strftime("%Y-%m-%d %H:%M:%S UTC")
    try:
        pdf = render_product_document_pdf(product, get_settings(),
                                          date.today().isoformat(), issued_at=issued_at)
    except TectonicNotFound as exc:
        return jsonify({"error": str(exc)}), 503
    _file_history_copy(product_id, pdf, stamp, issued_at)
    return Response(pdf, mimetype="application/pdf", headers={
        "Content-Disposition": 'inline; filename="' + product_id + '_product_document.pdf"',
    })


@product_bp.get("/<product_id>/pack.zip")
def product_pack(product_id: str):
    """The product's own document plus the full pack of every model it binds, zipped."""
    product = get_product(product_id)
    if product is None:
        return jsonify({"error": "product not found"}), 404
    try:
        data = build_product_pack(product, get_settings(), date.today().isoformat())
    except TectonicNotFound as exc:
        return jsonify({"error": str(exc)}), 503
    return Response(data, mimetype="application/zip", headers={
        "Content-Disposition": _attachment(PACK_NAME.format(product_id=product_id)),
    })


@product_bp.get("/<product_id>/pack-manifest")
def product_pack_manifest(product_id: str):
    """A cheap preview of what the pack would contain, without compiling any PDF."""
    product = get_product(product_id)
    if product is None:
        return jsonify({"error": "product not found"}), 404
    return jsonify(pack_manifest(product, get_settings()))
