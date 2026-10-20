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
"""Artefacts: the documents an institution PRODUCES, filed per division.

The Documents tab holds two different things. Bibliography is the external reference
material the framework is built on; Artefacts is the institution's own output — terms of
reference, committee presentations, the risk policy, the user guide. They are separated
because they answer different questions: one is what we read, the other is what we issue.

Filed per division (plus a company-wide shelf) because a division's terms of reference are
not another's, and because the risk policy already lives per division. Each artefact is an
uploaded file, so nothing here is in git — uploads live under UPLOAD_DIR.

A division is an aggregate id of its own rather than a field on one shared aggregate, so
adding a division adds a shelf rather than a filter, and one division's history is never
interleaved with another's.
"""
from __future__ import annotations

from flask import Blueprint, jsonify, request

from config.governance import ARTEFACT_KINDS, COMPANY_WIDE_SHELF
from src.files import UploadError, upload_path
from src.governance.documents import (
    GOVERNANCE_ARTEFACTS_AGGREGATE,
    add_document,
    find_document,
    list_documents,
    remove_document,
)
from src.governance.reference import get_reference_lists
from src.web._helpers import request_actor, send_document

artefacts_bp = Blueprint("artefacts", __name__, url_prefix="/api/artefacts")

_AGG = GOVERNANCE_ARTEFACTS_AGGREGATE


def _scope(shelf: str) -> str:
    """Where a shelf's files are stored on disk (mirrors ``model_scope``)."""
    return f"artefact/{shelf}"


def _shelves() -> list[str]:
    """The company-wide shelf first, then one per division."""
    divisions = [d.get("value") for d in (get_reference_lists().get("division") or [])
                 if d.get("value")]
    return [COMPANY_WIDE_SHELF, *divisions]


@artefacts_bp.get("")
def shelves():
    """Every shelf and what is filed on it, so the tab can draw its sub-tabs and tiles
    in one round trip."""
    return jsonify({
        "shelves": _shelves(),
        "kinds": list(ARTEFACT_KINDS),
        "artefacts": {shelf: list_documents(_AGG, shelf) for shelf in _shelves()},
    })


@artefacts_bp.post("/<shelf>")
def upload(shelf: str):
    """File an artefact on a shelf. ``kind`` says what sort of thing it is (Terms of
    Reference, Presentation, …) so the tiles can be read at a glance."""
    if shelf not in _shelves():
        return jsonify({"error": f"unknown shelf: {shelf}"}), 404
    file = request.files.get("file")
    if file is None:
        return jsonify({"error": "no file provided"}), 400
    kind = request.form.get("kind") or ""
    if kind and kind not in ARTEFACT_KINDS:
        return jsonify({"error": f"kind must be one of: {', '.join(ARTEFACT_KINDS)}"}), 400
    try:
        add_document(
            aggregate_type=_AGG, aggregate_id=shelf, scope=_scope(shelf),
            filename=file.filename, data=file.read(), category=kind,
            description=request.form.get("description", ""), actor=request_actor(),
        )
    except UploadError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify(list_documents(_AGG, shelf)), 201


@artefacts_bp.get("/<shelf>/<item_id>/download")
def download(shelf: str, item_id: str):
    doc = find_document(_AGG, shelf, item_id)
    if doc is None:
        return jsonify({"error": "artefact not found"}), 404
    path = upload_path(_scope(shelf), doc["filename"])
    if not path.exists():
        return jsonify({"error": "artefact file missing"}), 404
    return send_document(path, doc, inline=request.args.get("inline") == "1")


@artefacts_bp.post("/<shelf>/<item_id>/delete")
def delete(shelf: str, item_id: str):
    if find_document(_AGG, shelf, item_id) is None:
        return jsonify({"error": "artefact not found"}), 404
    remove_document(aggregate_type=_AGG, aggregate_id=shelf, item_id=item_id,
                    actor=request_actor())
    return jsonify(list_documents(_AGG, shelf))
