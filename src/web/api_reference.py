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
"""HTTP API for the admin-managed reference (menu) lists."""
from __future__ import annotations

from flask import Blueprint, jsonify, request, send_file

from config.governance import REFERENCE_SPECS
from src.command import dispatch
from src.files import UploadError, save_upload, upload_path
from src.governance.reference import add_option, get_reference_lists, remove_option, update_option
from src.web._helpers import (
    context_from_request,
    json_body,
    reference_options,
    request_actor,
    resolve_field,
)

reference_bp = Blueprint("reference", __name__, url_prefix="/api/reference")


def _specs():
    options = reference_options()
    return [
        {
            "key": key, "label": spec["label"], "id_prefix": spec["id_prefix"],
            "fields": [resolve_field(f, options) for f in spec["fields"]],
        }
        for key, spec in REFERENCE_SPECS.items()
    ]


@reference_bp.get("")
def lists():
    """The menu lists (with item ids) plus their specs, for the admin tab."""
    return jsonify({"data": get_reference_lists(), "collections": _specs()})


@reference_bp.post("/collections/<list_name>")
def add(list_name: str):
    body = json_body()
    dispatch(
        "add_option", add_option, context=context_from_request(body),
        list_name=list_name, fields=body.get("fields") or {},
    )
    return jsonify(get_reference_lists()), 201


@reference_bp.post("/collections/<list_name>/<item_id>")
def update(list_name: str, item_id: str):
    body = json_body()
    dispatch(
        "update_option", update_option, context=context_from_request(body),
        list_name=list_name, item_id=item_id, fields=body.get("fields") or {},
    )
    return jsonify(get_reference_lists())


@reference_bp.post("/collections/<list_name>/<item_id>/delete")
def remove(list_name: str, item_id: str):
    body = json_body()
    dispatch(
        "remove_option", remove_option, context=context_from_request(body),
        list_name=list_name, item_id=item_id,
    )
    return jsonify(get_reference_lists())


def _mrc_committee(item_id: str) -> dict | None:
    return next((i for i in get_reference_lists().get("mrc", [])
                 if i["item_id"] == item_id), None)


@reference_bp.post("/collections/mrc/<item_id>/tor")
def upload_mrc_tor(item_id: str):
    """Upload a committee's Terms of Reference; stored against that MRC entry."""
    if _mrc_committee(item_id) is None:
        return jsonify({"error": "unknown committee"}), 404
    file = request.files.get("file")
    if file is None:
        return jsonify({"error": "no file provided"}), 400
    try:
        meta = save_upload("mrc", file.filename, file.read())
    except UploadError as exc:
        return jsonify({"error": str(exc)}), 400
    update_option(
        list_name="mrc", item_id=item_id,
        fields={"tor_filename": meta["filename"], "tor_original_name": meta["original_name"]},
        actor=request_actor(),
    )
    return jsonify(get_reference_lists()), 201


@reference_bp.get("/collections/mrc/<item_id>/tor")
def download_mrc_tor(item_id: str):
    """Download a committee's Terms of Reference document, if uploaded."""
    item = _mrc_committee(item_id)
    if item is None or not item.get("tor_filename"):
        return jsonify({"error": "no ToR uploaded"}), 404
    path = upload_path("mrc", item["tor_filename"])
    if not path.exists():
        return jsonify({"error": "ToR file missing"}), 404
    return send_file(str(path), as_attachment=True,
                     download_name=item.get("tor_original_name") or "terms-of-reference")
