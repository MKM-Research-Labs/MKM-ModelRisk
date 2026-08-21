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
"""Documents for an ML Application: the uploaded evidence pack and the generated
ML Application Document.

The ML twin of ``api_product_documents``. The generated document is built on request
rather than stored, so it can never be a stale copy of the record, and every issued
copy is filed back against the record under History -- what the ML Application looked
like on the day the document went out.

Attaches to ``ml_application_bp`` to keep the ``/api/ml-applications`` URL space in
one place.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from flask import Response, jsonify, request

from config.governance import DOC_CATEGORIES, HISTORY_DOC_CATEGORY
from src.files import UploadError, upload_path
from src.governance.documents import (add_document, find_document,
                                      ml_application_scope, remove_document)
from src.governance.ml_application import get_ml_application, rebuild_ml_application_view
from src.governance.ml_application.commands import AGGREGATE_TYPE as ML_AGGREGATE
from src.governance.ml_application.document import render_ml_application_document_pdf
from src.governance.mrc.pack import TectonicNotFound
from src.governance.mrc_settings import get_settings
from src.web._helpers import request_actor, send_document
from src.web.api_ml_application import ml_application_bp


@ml_application_bp.post("/<ml_application_id>/documents")
def upload_document(ml_application_id: str):
    """Supporting Documentation: upload a categorised file against the record."""
    if get_ml_application(ml_application_id) is None:
        return jsonify({"error": "ML Application not found"}), 404
    category = request.form.get("category")
    if category not in DOC_CATEGORIES:
        return jsonify({"error": "invalid category"}), 400
    file = request.files.get("file")
    if file is None:
        return jsonify({"error": "no file provided"}), 400
    try:
        add_document(aggregate_type=ML_AGGREGATE, aggregate_id=ml_application_id,
                     scope=ml_application_scope(ml_application_id), category=category,
                     filename=file.filename, data=file.read(),
                     description=request.form.get("description", ""), actor=request_actor())
    except UploadError as exc:
        return jsonify({"error": str(exc)}), 400
    rebuild_ml_application_view()
    return jsonify(get_ml_application(ml_application_id)), 201


@ml_application_bp.get("/<ml_application_id>/documents/<item_id>/download")
def download_document(ml_application_id: str, item_id: str):
    doc = find_document(ML_AGGREGATE, ml_application_id, item_id)
    if doc is None:
        return jsonify({"error": "document not found"}), 404
    path = upload_path(ml_application_scope(ml_application_id), doc["filename"])
    if not path.exists():
        return jsonify({"error": "file missing"}), 404
    return send_document(path, doc, inline=request.args.get("inline") == "1")


@ml_application_bp.post("/<ml_application_id>/documents/<item_id>/delete")
def delete_document(ml_application_id: str, item_id: str):
    remove_document(aggregate_type=ML_AGGREGATE, aggregate_id=ml_application_id,
                    item_id=item_id, actor=request_actor())
    rebuild_ml_application_view()
    return jsonify(get_ml_application(ml_application_id))


def _file_history_copy(ml_application_id: str, pdf: bytes, stamp: str, issued_at: str) -> None:
    """File the issued document against the record under History, so every issued
    version is kept -- the copy records what the ML Application looked like when the
    document went out, exactly as a model's and a product's do."""
    name = f"{ml_application_id}_ml_application_document_{stamp}.pdf"
    add_document(aggregate_type=ML_AGGREGATE, aggregate_id=ml_application_id,
                 scope=ml_application_scope(ml_application_id),
                 category=HISTORY_DOC_CATEGORY, filename=name, data=pdf,
                 description="ML Application Document issued " + issued_at,
                 actor=request_actor())
    rebuild_ml_application_view()


@ml_application_bp.get("/<ml_application_id>/document.pdf")
def ml_application_document(ml_application_id: str):
    """The record's ML Application Document, generated on request and filed under
    History so every issued version is kept."""
    record = get_ml_application(ml_application_id)
    if record is None:
        return jsonify({"error": "ML Application not found"}), 404
    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y-%m-%dT%H%M%S.%f")[:-3] + "Z"
    issued_at = now.strftime("%Y-%m-%d %H:%M:%S UTC")
    try:
        pdf = render_ml_application_document_pdf(record, get_settings(),
                                                 date.today().isoformat(),
                                                 issued_at=issued_at)
    except TectonicNotFound as exc:
        return jsonify({"error": str(exc)}), 503
    _file_history_copy(ml_application_id, pdf, stamp, issued_at)
    return Response(pdf, mimetype="application/pdf", headers={
        "Content-Disposition":
            'inline; filename="' + ml_application_id + '_ml_application_document.pdf"',
    })
