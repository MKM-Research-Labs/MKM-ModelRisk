# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

#
# This software is provided under license by MKM Research Labs.
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

"""Governance document upload/download/delete routes."""

import os
import uuid
from datetime import datetime

from flask import jsonify, request, send_file
from werkzeug.utils import secure_filename

from . import _constants, governance_bp
from ._constants import ALLOWED_UPLOAD_EXTENSIONS, MAX_UPLOAD_SIZE
from ._helpers import (
    _load_gov_documents, _save_gov_documents,
    _discover_audit_docs, _discover_model_docs,
)


@governance_bp.route("/governance/documents", methods=["GET"])
def get_documents():
    """List all governance documents (uploaded + auto-discovered)."""
    uploaded = _load_gov_documents()
    for doc in uploaded:
        doc.setdefault("source", "uploaded")

    audit_docs = _discover_audit_docs()
    model_docs = _discover_model_docs()

    all_docs = uploaded + audit_docs + model_docs
    return jsonify({"status": "success", "documents": all_docs})


@governance_bp.route("/governance/documents/upload", methods=["POST"])
def upload_document():
    """Upload a governance document."""
    if "file" not in request.files:
        return jsonify({"status": "error", "message": "No file provided"}), 400

    f = request.files["file"]
    if not f.filename:
        return jsonify({"status": "error", "message": "No file selected"}), 400

    # Validate file extension
    ext = os.path.splitext(f.filename)[1].lstrip('.').lower()
    if ext not in ALLOWED_UPLOAD_EXTENSIONS:
        return jsonify({"status": "error", "message": f"File type '.{ext}' not allowed"}), 400

    # Validate file size
    f.seek(0, 2)
    size = f.tell()
    f.seek(0)
    if size > MAX_UPLOAD_SIZE:
        return jsonify({"status": "error", "message": "File exceeds 50 MB limit"}), 413

    os.makedirs(_constants.GOV_DOCUMENTS_DIR, exist_ok=True)

    doc_id = str(uuid.uuid4())[:8]
    filename = secure_filename(f.filename)
    save_path = os.path.join(_constants.GOV_DOCUMENTS_DIR, f"{doc_id}_{filename}")
    f.save(save_path)

    doc_entry = {
        "id": doc_id,
        "filename": filename,
        "stored_as": f"{doc_id}_{filename}",
        "description": request.form.get("description", ""),
        "uploaded_at": datetime.now().isoformat(),
        "size": os.path.getsize(save_path),
    }

    docs = _load_gov_documents()
    docs.append(doc_entry)
    if not _save_gov_documents(docs):
        return jsonify({"status": "error", "message": "Failed to save metadata"}), 500

    return jsonify({"status": "success", "document": doc_entry})


@governance_bp.route("/governance/documents/<doc_id>/download", methods=["GET"])
def download_document(doc_id):
    """Download a governance document."""
    docs = _load_gov_documents()
    doc = next((d for d in docs if d["id"] == doc_id), None)
    if not doc:
        return jsonify({"status": "error", "message": "Document not found"}), 404

    file_path = os.path.join(_constants.GOV_DOCUMENTS_DIR, doc["stored_as"])
    if not os.path.isfile(file_path):
        return jsonify({"status": "error", "message": "File not found on disk"}), 404

    return send_file(file_path, as_attachment=True, download_name=doc["filename"])


@governance_bp.route("/governance/documents/<doc_id>/delete", methods=["POST"])
def delete_document(doc_id):
    """Delete a governance document."""
    docs = _load_gov_documents()
    doc = next((d for d in docs if d["id"] == doc_id), None)
    if not doc:
        return jsonify({"status": "error", "message": "Document not found"}), 404

    # Remove file
    file_path = os.path.join(_constants.GOV_DOCUMENTS_DIR, doc["stored_as"])
    if os.path.isfile(file_path):
        os.remove(file_path)

    docs = [d for d in docs if d["id"] != doc_id]
    if not _save_gov_documents(docs):
        return jsonify({"status": "error", "message": "Failed to save metadata"}), 500

    return jsonify({"status": "success"})
