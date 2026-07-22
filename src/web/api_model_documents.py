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

from datetime import date

from flask import Response, jsonify

from src.governance.model_inventory import get_model, list_models
from src.governance.model_inventory.client_pack import PACK_NAME, build_model_pack
from src.governance.model_inventory.document import render_model_document_pdf
from src.governance.model_inventory.report import render_report_pdf
from src.governance.mrc_settings import get_settings
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


@models_bp.get("/<model_id>/risk-document.pdf")
def model_risk_document(model_id: str):
    """One model's client-facing Model Risk Document, generated on request."""
    model = get_model(model_id)
    if model is None:
        return jsonify({"error": "model not found"}), 404
    pdf = render_model_document_pdf(model, get_settings(), date.today().isoformat())
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
