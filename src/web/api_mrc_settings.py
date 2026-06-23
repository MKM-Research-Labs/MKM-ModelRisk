# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
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
from src.governance.mrc_settings import get_settings, set_field, set_logo
from src.web._helpers import context_from_request, json_body, request_actor

settings_bp = Blueprint("mrc_settings", __name__, url_prefix="/api/mrc")


def _specs():
    return [
        {"key": s["key"], "label": s["label"], "type": s["type"], "options": list(s.get("options", []))}
        for s in MRC_SETTINGS_SPECS
    ]


@settings_bp.get("/settings")
def get():
    settings = get_settings()
    return jsonify({"fields": settings["fields"], "logo": settings["logo"], "specs": _specs()})


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
