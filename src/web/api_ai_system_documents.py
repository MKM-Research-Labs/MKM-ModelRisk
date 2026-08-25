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
"""Documents for an AI System: the uploaded evidence pack.

Attaches to ``ai_system_bp`` to keep the ``/api/ai-systems`` URL space in one place,
exactly as the ML Application's documents do.

No generated AI System Document yet. A model, a product and an ML Application each
render one from the record on request; this record type does not, and the reason is
worth stating rather than leaving as an omission somebody trips over: the document is
the thing a committee is handed, and what an AI System's should contain is a
governance question rather than a template question. It arrives with the pack work,
not before it.
"""
from __future__ import annotations

from flask import jsonify, request

from config.governance import DOC_CATEGORIES
from src.files import UploadError, upload_path
from src.governance.ai_system import get_ai_system, rebuild_ai_system_view
from src.governance.ai_system.commands import AGGREGATE_TYPE as AI_AGGREGATE
from src.governance.documents import (add_document, ai_system_scope, find_document,
                                      remove_document)
from src.web._helpers import request_actor, send_document
from src.web.api_ai_system import ai_system_bp


@ai_system_bp.post("/<ai_system_id>/documents")
def upload_document(ai_system_id: str):
    """Supporting Documentation: upload a categorised file against the record."""
    if get_ai_system(ai_system_id) is None:
        return jsonify({"error": "AI System not found"}), 404
    category = request.form.get("category")
    if category not in DOC_CATEGORIES:
        return jsonify({"error": "invalid category"}), 400
    file = request.files.get("file")
    if file is None:
        return jsonify({"error": "no file provided"}), 400
    try:
        add_document(aggregate_type=AI_AGGREGATE, aggregate_id=ai_system_id,
                     scope=ai_system_scope(ai_system_id), category=category,
                     filename=file.filename, data=file.read(),
                     description=request.form.get("description", ""),
                     actor=request_actor())
    except UploadError as exc:
        return jsonify({"error": str(exc)}), 400
    rebuild_ai_system_view()
    return jsonify(get_ai_system(ai_system_id)), 201


@ai_system_bp.get("/<ai_system_id>/documents/<item_id>/download")
def download_document(ai_system_id: str, item_id: str):
    doc = find_document(AI_AGGREGATE, ai_system_id, item_id)
    if doc is None:
        return jsonify({"error": "document not found"}), 404
    path = upload_path(ai_system_scope(ai_system_id), doc["filename"])
    if not path.exists():
        return jsonify({"error": "file missing"}), 404
    return send_document(path, doc, inline=request.args.get("inline") == "1")


@ai_system_bp.post("/<ai_system_id>/documents/<item_id>/delete")
def delete_document(ai_system_id: str, item_id: str):
    remove_document(aggregate_type=AI_AGGREGATE, aggregate_id=ai_system_id,
                    item_id=item_id, actor=request_actor())
    rebuild_ai_system_view()
    return jsonify(get_ai_system(ai_system_id))
