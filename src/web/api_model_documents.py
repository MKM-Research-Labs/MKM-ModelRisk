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
"""Generated outputs for the model inventory: the reports, documents and packs.

These endpoints produce a file rather than read or write the inventory, and every
one of them is built on request so it can never be a stale copy of the record. They
attach to ``models_bp`` (as the sign-off endpoints do) to keep the ``/api/models``
URL space in one place while leaving the inventory API itself uncluttered.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from flask import Response, jsonify

from config.files import HIDDEN_DOC_EXTENSIONS
from config.governance import HISTORY_DOC_CATEGORY, MRC_REVIEWABLE_CATEGORIES
from src.files import extension
from src.governance.documents import add_document, model_scope
from src.governance.model_inventory import get_model, list_models, rebuild_inventory_view
from src.governance.model_inventory.commands import AGGREGATE_TYPE as MODEL_AGGREGATE
from src.governance.model_inventory.client_pack import PACK_NAME, build_model_pack
from src.governance.model_inventory.document import render_model_document_pdf
from src.governance.model_inventory.report import render_report_pdf
from src.governance.mrc_settings import get_settings
from src.web._helpers import request_actor
from src.web.api_models import models_bp


def _attachment(name: str) -> str:
    return 'attachment; filename="' + name + '"'


@models_bp.get("/risk-report.pdf")
def risk_report():
    """The Model Risk Report: the whole inventory, for the committee."""
    pdf = render_report_pdf(list_models(), get_settings(), date.today().isoformat())
    return Response(pdf, mimetype="application/pdf", headers={
        "Content-Disposition": 'inline; filename="model_risk_report.pdf"',
    })


def _file_history_copy(model_id: str, pdf: bytes, stamp: str, issued_at: str) -> None:
    """File the issued document against the model under History.

    Each issue is kept, timestamped, because the document renders the inventory as
    it stood at that moment: the filed copy is what the model looked like when the
    document went out. That is the second time axis — the audit trail records when
    we were told something, these record what we said, and when.
    """
    name = f"{model_id}_model_risk_document_{stamp}.pdf"
    add_document(aggregate_type=MODEL_AGGREGATE, aggregate_id=model_id,
                 scope=model_scope(model_id), category=HISTORY_DOC_CATEGORY,
                 filename=name, data=pdf,
                 description="Model Risk Document issued " + issued_at,
                 actor=request_actor())
    rebuild_inventory_view()


@models_bp.get("/<model_id>/risk-document.pdf")
def model_risk_document(model_id: str):
    """One model's client-facing Model Risk Document, generated on request and
    filed under History so every issued version is kept."""
    model = get_model(model_id)
    if model is None:
        return jsonify({"error": "model not found"}), 404
    now = datetime.now(timezone.utc)
    # Two stamps from one instant: a filename-safe one for the filed copy and a
    # readable one printed on the paper, so the History row and the document it
    # points at agree. Milliseconds, not seconds — two issues a moment apart (a
    # double-click) would otherwise share a filename and the second would
    # overwrite the first while both rows claimed to be distinct versions.
    stamp = now.strftime("%Y-%m-%dT%H%M%S.%f")[:-3] + "Z"
    issued_at = now.strftime("%Y-%m-%d %H:%M:%S UTC")
    pdf = render_model_document_pdf(model, get_settings(), date.today().isoformat(),
                                    issued_at=issued_at)
    _file_history_copy(model_id, pdf, stamp, issued_at)
    return Response(pdf, mimetype="application/pdf", headers={
        "Content-Disposition": 'inline; filename="' + model_id + '_model_risk_document.pdf"',
    })


@models_bp.get("/<model_id>/pack.zip")
def model_client_pack(model_id: str):
    """The model's risk document plus its PDF evidence, zipped for sending on."""
    model = get_model(model_id)
    if model is None:
        return jsonify({"error": "model not found"}), 404
    data = build_model_pack(model, get_settings(), date.today().isoformat())
    return Response(data, mimetype="application/zip", headers={
        "Content-Disposition": _attachment(PACK_NAME.format(model_id=model_id)),
    })


@models_bp.get("/<model_id>/reviewable-documents")
def reviewable_documents(model_id: str):
    """The model's documents an MRC can table for review.

    The paper lives on the model; a meeting references it rather than holding its
    own copy, so a committee always reviews what the model actually holds and the
    two cannot drift apart.
    """
    model = get_model(model_id)
    if model is None:
        return jsonify({"error": "model not found"}), 404
    docs = (model["data"] or {}).get("documents") or []
    return jsonify([
        {"item_id": d.get("item_id"), "category": d.get("category"),
         "original_name": d.get("original_name")}
        for d in docs
        if isinstance(d, dict) and d.get("category") in MRC_REVIEWABLE_CATEGORIES
        # The LaTeX source filed beside a PDF is the same paper in a form no
        # committee reads, so it is not offered for tabling either.
        and extension(d.get("original_name", "")) not in HIDDEN_DOC_EXTENSIONS
    ])
