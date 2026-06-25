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
"""HTTP API for the PVM aggregate."""
from __future__ import annotations

from flask import Blueprint, jsonify

from config.governance import PVM_BINDINGS, PVM_COLLECTION_SPECS, PVM_FIELD_SPECS, PVM_REGISTER_FIELDS
from src.command import dispatch
from src.governance.model_inventory import list_models
from src.governance.pvm import (
    add_collection_item,
    get_pvm,
    list_pvms,
    rebind_component,
    rebuild_pvm_view,
    register_pvm,
    remove_collection_item,
    retire_pvm,
    update_collection_item,
    update_pvm_field,
)
from src.web._helpers import context_from_request, json_body, reference_options

pvm_bp = Blueprint("pvm", __name__, url_prefix="/api/pvms")


def _grouped_specs(options: dict[str, list], model_ids: list[str]):
    """Field specs grouped for the detail view; bindings resolve to dropdowns."""
    groups: list[dict] = []
    by_name: dict[str, dict] = {}
    for key, spec in PVM_FIELD_SPECS.items():
        group = by_name.get(spec["group"])
        if group is None:
            group = {"group": spec["group"], "fields": []}
            by_name[spec["group"]] = group
            groups.append(group)
        field_type, choices = spec["type"], list(spec.get("options", []))
        if key == "analytics_model":
            field_type, choices = "choice", model_ids
        else:
            reference = spec.get("reference")
            if reference and options.get(reference):
                field_type, choices = "choice", options[reference]
        group["fields"].append(
            {"key": key, "label": spec["label"], "type": field_type, "options": choices})
    return groups


def _collection_specs():
    return [
        {"key": key, "label": spec["label"], "id_prefix": spec["id_prefix"],
         "fields": [{"key": f["key"], "label": f["label"], "type": f["type"],
                     "options": list(f.get("options", [])), "required": bool(f.get("required"))}
                    for f in spec["fields"]]}
        for key, spec in PVM_COLLECTION_SPECS.items()
    ]


@pvm_bp.get("/fields")
def field_specs():
    live_models = [m["model_id"] for m in list_models() if not m["retired"]]
    return jsonify({
        "groups": _grouped_specs(reference_options(), live_models),
        "register": list(PVM_REGISTER_FIELDS),
        "bindings": list(PVM_BINDINGS),
        "collections": _collection_specs(),
    })


@pvm_bp.get("")
def list_all():
    return jsonify(list_pvms())


@pvm_bp.get("/used-by/<model_id>")
def used_by(model_id: str):
    """PVMs whose Analytics Model is ``model_id`` (lineage)."""
    return jsonify([p for p in list_pvms() if p["data"].get("analytics_model") == model_id])


@pvm_bp.get("/<pvm_id>")
def get_one(pvm_id: str):
    pvm = get_pvm(pvm_id)
    if pvm is None:
        return jsonify({"error": "PVM not found"}), 404
    return jsonify(pvm)


@pvm_bp.post("")
def register():
    body = json_body()
    dispatch(
        "register_pvm", register_pvm, context=context_from_request(body),
        pvm_id=body.get("pvm_id"), product=body.get("product"), fields=body.get("fields") or {})
    rebuild_pvm_view()
    return jsonify(get_pvm(body.get("pvm_id"))), 201


@pvm_bp.post("/<pvm_id>/field")
def update_field(pvm_id: str):
    body = json_body()
    dispatch(
        "update_pvm_field", update_pvm_field, context=context_from_request(body),
        pvm_id=pvm_id, field=body.get("field"), value=body.get("value"))
    rebuild_pvm_view()
    return jsonify(get_pvm(pvm_id))


@pvm_bp.post("/<pvm_id>/rebind")
def rebind(pvm_id: str):
    body = json_body()
    dispatch(
        "rebind_component", rebind_component, context=context_from_request(body),
        pvm_id=pvm_id, component=body.get("component"), value=body.get("value"))
    rebuild_pvm_view()
    return jsonify(get_pvm(pvm_id))


@pvm_bp.post("/<pvm_id>/retire")
def retire(pvm_id: str):
    body = json_body()
    dispatch("retire_pvm", retire_pvm, context=context_from_request(body), pvm_id=pvm_id)
    rebuild_pvm_view()
    return jsonify(get_pvm(pvm_id))


@pvm_bp.post("/<pvm_id>/collections/<collection>")
def add_item(pvm_id: str, collection: str):
    body = json_body()
    dispatch(
        "add_collection_item", add_collection_item, context=context_from_request(body),
        pvm_id=pvm_id, collection=collection, fields=body.get("fields") or {})
    rebuild_pvm_view()
    return jsonify(get_pvm(pvm_id)), 201


@pvm_bp.post("/<pvm_id>/collections/<collection>/<item_id>")
def update_item(pvm_id: str, collection: str, item_id: str):
    body = json_body()
    dispatch(
        "update_collection_item", update_collection_item, context=context_from_request(body),
        pvm_id=pvm_id, collection=collection, item_id=item_id, fields=body.get("fields") or {})
    rebuild_pvm_view()
    return jsonify(get_pvm(pvm_id))


@pvm_bp.post("/<pvm_id>/collections/<collection>/<item_id>/delete")
def delete_item(pvm_id: str, collection: str, item_id: str):
    body = json_body()
    dispatch(
        "remove_collection_item", remove_collection_item, context=context_from_request(body),
        pvm_id=pvm_id, collection=collection, item_id=item_id)
    rebuild_pvm_view()
    return jsonify(get_pvm(pvm_id))
