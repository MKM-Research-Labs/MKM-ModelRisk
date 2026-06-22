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
"""HTTP API for the admin-managed reference (menu) lists."""
from __future__ import annotations

from flask import Blueprint, jsonify

from config.governance import REFERENCE_SPECS
from src.command import dispatch
from src.governance.reference import add_option, get_reference_lists, remove_option
from src.web._helpers import context_from_request, json_body

reference_bp = Blueprint("reference", __name__, url_prefix="/api/reference")


def _specs():
    return [
        {
            "key": key, "label": spec["label"], "id_prefix": spec["id_prefix"],
            "fields": [
                {"key": f["key"], "label": f["label"], "type": f["type"],
                 "options": [], "required": bool(f.get("required"))}
                for f in spec["fields"]
            ],
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


@reference_bp.post("/collections/<list_name>/<item_id>/delete")
def remove(list_name: str, item_id: str):
    body = json_body()
    dispatch(
        "remove_option", remove_option, context=context_from_request(body),
        list_name=list_name, item_id=item_id,
    )
    return jsonify(get_reference_lists())
