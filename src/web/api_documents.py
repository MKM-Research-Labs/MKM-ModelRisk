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
"""HTTP API for governance-wide documents (the top-level Documents tab)."""
from __future__ import annotations

from flask import Blueprint, jsonify, request, send_file

from src.files import UploadError, upload_path
from src.governance.documents import (
    add_document,
    clean_model_types,
    find_document,
    list_documents,
    remove_document,
    update_document,
)
from src.web._helpers import request_actor

documents_bp = Blueprint("documents", __name__, url_prefix="/api/documents")

_AGG = "GovernanceDocuments"
_ID = "global"
_SCOPE = "governance"
# What an amended field is called in the audit trail's reason line.
_FIELD_LABELS = {"model_types": "model types", "description": "description"}


@documents_bp.get("")
def list_all():
    return jsonify(list_documents(_AGG, _ID))


@documents_bp.post("")
def upload():
    file = request.files.get("file")
    if file is None:
        return jsonify({"error": "no file provided"}), 400
    try:
        add_document(
            aggregate_type=_AGG, aggregate_id=_ID, scope=_SCOPE, filename=file.filename,
            data=file.read(), description=request.form.get("description", ""),
            model_types=request.form.getlist("model_types"), actor=request_actor(),
        )
    except UploadError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify(list_documents(_AGG, _ID)), 201


@documents_bp.post("/<item_id>/metadata")
@documents_bp.post("/<item_id>/model-types")
def set_metadata(item_id: str):
    """Amend an external document's description and model-type tags.

    Metadata only: the file on disk and the item id stay put. Fields absent from
    the body are left alone rather than cleared, so a caller that knows about only
    one of them (the older ``/model-types`` path, kept as an alias) cannot wipe the
    other by omission.
    """
    if find_document(_AGG, _ID, item_id) is None:
        return jsonify({"error": "document not found"}), 404
    body = request.get_json(silent=True) or {}
    fields = {}
    if "model_types" in body:
        fields["model_types"] = clean_model_types(body.get("model_types"))
    if "description" in body:
        fields["description"] = str(body.get("description") or "").strip()
    if not fields:
        return jsonify({"error": "no metadata to amend"}), 400
    update_document(
        aggregate_type=_AGG, aggregate_id=_ID, item_id=item_id, fields=fields,
        actor=request_actor(),
        reason="Set document " + " and ".join(_FIELD_LABELS[k] for k in fields),
    )
    return jsonify(list_documents(_AGG, _ID))


@documents_bp.get("/<item_id>/download")
def download(item_id: str):
    doc = find_document(_AGG, _ID, item_id)
    if doc is None:
        return jsonify({"error": "document not found"}), 404
    path = upload_path(_SCOPE, doc["filename"])
    if not path.exists():
        return jsonify({"error": "file missing"}), 404
    return send_file(str(path), as_attachment=True, download_name=doc["original_name"])


@documents_bp.post("/<item_id>/delete")
def delete(item_id: str):
    remove_document(aggregate_type=_AGG, aggregate_id=_ID, item_id=item_id, actor=request_actor())
    return jsonify(list_documents(_AGG, _ID))
