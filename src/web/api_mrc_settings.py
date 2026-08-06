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
"""HTTP API for MRC settings + branding (org details, logo)."""
from __future__ import annotations

from flask import Blueprint, jsonify, request, send_file

from config.governance import MRC_SETTINGS_SPECS
from src.command import dispatch
from src.files import UploadError, save_upload, upload_path
from src.governance.mrc_settings import get_settings, set_field, set_logo, set_tor
from src.web._helpers import context_from_request, json_body, request_actor

settings_bp = Blueprint("mrc_settings", __name__, url_prefix="/api/mrc")


def _specs():
    return [
        {"key": s["key"], "label": s["label"], "type": s["type"],
         "options": list(s.get("options", [])),
         # Which Admin sub-tab owns this setting ("misc", or the MRC detail when unset).
         "group": s.get("group", "")}
        for s in MRC_SETTINGS_SPECS
    ]


@settings_bp.get("/settings")
def get():
    settings = get_settings()
    return jsonify({
        "fields": settings["fields"], "logo": settings["logo"],
        "tor": settings.get("tor"), "specs": _specs(),
    })


@settings_bp.post("/settings/field")
def update_field():
    body = json_body()
    dispatch(
        "set_mrc_setting", set_field, context=context_from_request(body),
        field=body.get("field"), value=body.get("value"),
    )
    return jsonify(get_settings())


@settings_bp.post("/settings/logo")
def upload_logo():
    file = request.files.get("file")
    if file is None:
        return jsonify({"error": "no file provided"}), 400
    try:
        meta = save_upload("mrc", file.filename, file.read())
    except UploadError as exc:
        return jsonify({"error": str(exc)}), 400
    set_logo(filename=meta["filename"], original_name=meta["original_name"], actor=request_actor())
    return jsonify(get_settings()), 201


@settings_bp.get("/logo")
def logo():
    settings = get_settings()
    path = upload_path("mrc", settings["logo"]["filename"]) if settings["logo"] else None
    if path is None or not path.exists():
        return jsonify({"error": "no logo"}), 404
    return send_file(str(path))


@settings_bp.post("/settings/tor")
def upload_tor():
    """Upload the MRC Terms of Reference document (typically a .docx or .pdf)."""
    file = request.files.get("file")
    if file is None:
        return jsonify({"error": "no file provided"}), 400
    try:
        meta = save_upload("mrc", file.filename, file.read())
    except UploadError as exc:
        return jsonify({"error": str(exc)}), 400
    set_tor(filename=meta["filename"], original_name=meta["original_name"], actor=request_actor())
    return jsonify(get_settings()), 201


@settings_bp.get("/tor")
def tor():
    """Download the current MRC Terms of Reference document, if uploaded."""
    settings = get_settings()
    if not settings.get("tor"):
        return jsonify({"error": "no ToR uploaded"}), 404
    path = upload_path("mrc", settings["tor"]["filename"])
    if not path.exists():
        return jsonify({"error": "ToR file missing"}), 404
    return send_file(str(path), as_attachment=True, download_name=settings["tor"]["original_name"])
