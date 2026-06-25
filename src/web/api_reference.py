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
from src.governance.reference import add_option, get_reference_lists, remove_option, update_option
from src.web._helpers import context_from_request, json_body, reference_options

reference_bp = Blueprint("reference", __name__, url_prefix="/api/reference")


def _field_spec(field: dict, options: dict[str, list]) -> dict:
    # A field backed by another list (e.g. a Division's Company, or an Owner)
    # becomes a dropdown once that list has values.
    reference = field.get("reference")
    if reference and options.get(reference):
        return {"key": field["key"], "label": field["label"], "type": "choice",
                "options": options[reference], "required": bool(field.get("required"))}
    # Otherwise keep the field's own type and any static options (e.g. a choice
    # field like the Market Data Model's update frequency).
    return {"key": field["key"], "label": field["label"], "type": field["type"],
            "options": list(field.get("options", [])), "required": bool(field.get("required"))}


def _specs():
    options = reference_options()
    return [
        {
            "key": key, "label": spec["label"], "id_prefix": spec["id_prefix"],
            "fields": [_field_spec(f, options) for f in spec["fields"]],
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
