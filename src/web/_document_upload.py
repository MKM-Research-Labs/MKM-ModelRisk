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
"""Filing a categorised document from a request: an uploaded file or a link.

Models, Products, ML Applications and AI Systems all take documents the same way,
from the same console panel, so the request is read in one place. A form carrying
``url`` files a link (``title`` optional); otherwise it must carry ``file``. Either
way the result is one document under the category given, and nothing downstream
treats the two differently.
"""
from __future__ import annotations

from flask import jsonify, request

from config.governance import DOC_CATEGORIES
from src.files import UploadError
from src.governance.document_links import add_link
from src.governance.documents import add_document
from src.web._helpers import request_actor


def file_document(*, aggregate_type: str, aggregate_id: str, scope: str):
    """File the request's document against the aggregate.

    Returns ``None`` once it is recorded, or the error response to send back.
    """
    category = request.form.get("category")
    if category not in DOC_CATEGORIES:
        return jsonify({"error": "invalid category"}), 400
    common = dict(aggregate_type=aggregate_type, aggregate_id=aggregate_id, scope=scope,
                  category=category, description=request.form.get("description", ""),
                  actor=request_actor())
    url = (request.form.get("url") or "").strip()
    file = request.files.get("file")
    if not url and file is None:
        return jsonify({"error": "no file or link provided"}), 400
    try:
        if url:
            add_link(url=url, title=request.form.get("title", ""), **common)
        else:
            add_document(filename=file.filename, data=file.read(), **common)
    except UploadError as exc:
        return jsonify({"error": str(exc)}), 400
    return None
