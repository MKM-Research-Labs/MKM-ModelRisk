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
"""Vendor documents: what a third-party supplier gives us, filed per vendor.

The third panel of the Documents tab. Bibliography is what the framework is built on
and Artefacts is what this institution issues; a vendor document is neither — it is
what a supplier hands over about its own product (a contract, an assurance report,
the vendor's own model documentation). It is evidence about the vendor rather than
about any one of our models, so it is filed against the vendor and outlives the
models that happen to use it.

A vendor is an aggregate id of its own, for the reason an artefact shelf is (see
api_artefacts): adding a vendor in Admin adds somewhere to file rather than one more
value to filter on, and one vendor's history is never interleaved with another's.
The vendor list is the Admin-defined one (Admin > Vendor, the same strict list a
model's ``vendor`` field picks from), so a document can only be filed against a
vendor the institution has actually declared.

The aggregate id is the reference item's id, not its name: renaming a vendor in Admin
is a relabelling, and its documents have to survive it.
"""
from __future__ import annotations

from flask import Blueprint, jsonify, request

from config.governance import VENDOR_LIST
from src.files import UploadError, upload_path
from src.governance.documents import (
    add_document,
    find_document,
    list_documents,
    remove_document,
)
from src.governance.reference import get_reference_lists
from src.web._helpers import request_actor, send_document

vendor_documents_bp = Blueprint("vendor_documents", __name__,
                                url_prefix="/api/vendor-documents")

_AGG = "GovernanceVendorDocuments"


def _scope(vendor_id: str) -> str:
    """Where a vendor's uploaded files live (mirrors ``model_scope``). Keyed on the
    reference id, which is safe as a path segment and stable across a rename."""
    return f"vendor/{vendor_id}"


def _vendors() -> list[dict]:
    """The Admin-defined vendors, as ``{vendor_id, name}`` in reference order."""
    return [{"vendor_id": item["item_id"], "name": item.get("value", "")}
            for item in (get_reference_lists().get(VENDOR_LIST) or [])
            if item.get("value")]


def _known(vendor_id: str) -> bool:
    return any(v["vendor_id"] == vendor_id for v in _vendors())


@vendor_documents_bp.get("")
def index():
    """Every vendor and what is filed against it, so the panel can draw its picker
    and its table in one round trip."""
    vendors = _vendors()
    return jsonify({
        "vendors": vendors,
        "documents": {v["vendor_id"]: list_documents(_AGG, v["vendor_id"]) for v in vendors},
    })


@vendor_documents_bp.post("/<vendor_id>")
def upload(vendor_id: str):
    """File a document against a vendor."""
    if not _known(vendor_id):
        return jsonify({"error": f"unknown vendor: {vendor_id}"}), 404
    file = request.files.get("file")
    if file is None:
        return jsonify({"error": "no file provided"}), 400
    try:
        add_document(
            aggregate_type=_AGG, aggregate_id=vendor_id, scope=_scope(vendor_id),
            filename=file.filename, data=file.read(),
            description=request.form.get("description", ""), actor=request_actor(),
        )
    except UploadError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify(list_documents(_AGG, vendor_id)), 201


@vendor_documents_bp.get("/<vendor_id>/<item_id>/download")
def download(vendor_id: str, item_id: str):
    doc = find_document(_AGG, vendor_id, item_id)
    if doc is None:
        return jsonify({"error": "vendor document not found"}), 404
    path = upload_path(_scope(vendor_id), doc["filename"])
    if not path.exists():
        return jsonify({"error": "vendor document file missing"}), 404
    return send_document(path, doc, inline=request.args.get("inline") == "1")


@vendor_documents_bp.post("/<vendor_id>/<item_id>/delete")
def delete(vendor_id: str, item_id: str):
    if find_document(_AGG, vendor_id, item_id) is None:
        return jsonify({"error": "vendor document not found"}), 404
    remove_document(aggregate_type=_AGG, aggregate_id=vendor_id, item_id=item_id,
                    actor=request_actor())
    return jsonify(list_documents(_AGG, vendor_id))
