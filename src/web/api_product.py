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
"""HTTP API for the Product aggregate."""
from __future__ import annotations

from flask import Blueprint, jsonify, request

from config.governance import (
    DOC_CATEGORIES,
    PRODUCT_BINDINGS,
    PRODUCT_COLLECTION_SPECS,
    PRODUCT_FIELD_SPECS,
    PRODUCT_REGISTER_FIELDS,
)
from src.command import dispatch
from src.files import UploadError, upload_path
from src.governance.documents import add_document, find_document, remove_document
from src.governance.model_inventory import list_models
from src.governance.product import (
    add_collection_item,
    get_product,
    list_products,
    rebind_component,
    rebuild_product_view,
    register_product,
    remove_collection_item,
    retire_product,
    update_collection_item,
    update_product_field,
)
from src.governance.product.commands import AGGREGATE_TYPE as PRODUCT_AGGREGATE
from src.web._helpers import (
    context_from_request,
    json_body,
    reference_options,
    request_actor,
    document_specs,
    resolve_field,
    send_document,
)

product_bp = Blueprint("product", __name__, url_prefix="/api/products")


def _product_scope(product_id: str) -> str:
    return f"product/{product_id}"


def _grouped_specs(options: dict[str, list], inventory_ids: dict[str, list[str]]):
    """Field specs grouped for the detail view; bindings resolve to dropdowns.

    ``inventory_ids`` maps each inventory-backed binding ("analytics_model",
    "market_data_model") to the list of eligible model IDs.
    """
    groups: list[dict] = []
    by_name: dict[str, dict] = {}
    for key, spec in PRODUCT_FIELD_SPECS.items():
        group = by_name.get(spec["group"])
        if group is None:
            group = {"group": spec["group"], "fields": []}
            by_name[spec["group"]] = group
            groups.append(group)
        field_type, choices = spec["type"], list(spec.get("options", []))
        if key in inventory_ids:
            field_type, choices = "choice", inventory_ids[key]
        else:
            reference = spec.get("reference")
            if reference and options.get(reference):
                field_type, choices = "choice", options[reference]
        group["fields"].append(
            {"key": key, "label": spec["label"], "type": field_type, "options": choices})
    return groups


def _collection_specs():
    options_by_list = reference_options()
    return [
        {"key": key, "label": spec["label"], "id_prefix": spec["id_prefix"],
         "fields": [resolve_field(f, options_by_list) for f in spec["fields"]]}
        for key, spec in PRODUCT_COLLECTION_SPECS.items()
    ]


@product_bp.get("/fields")
def field_specs():
    # A Product's analytics engine is any live model that isn't a Market Data
    # Model; its market-data binding is a live model of type "Market Data Model".
    live = [m for m in list_models() if not m["retired"]]
    inventory_ids = {
        "analytics_model": [
            m["model_id"] for m in live if (m["data"] or {}).get("type") != "Market Data Model"],
        "market_data_model": [
            m["model_id"] for m in live if (m["data"] or {}).get("type") == "Market Data Model"],
    }
    return jsonify({
        "groups": _grouped_specs(reference_options(), inventory_ids),
        "register": list(PRODUCT_REGISTER_FIELDS),
        "bindings": list(PRODUCT_BINDINGS),
        "collections": _collection_specs(),
        **document_specs(),
    })


@product_bp.get("")
def list_all():
    return jsonify(list_products())


@product_bp.get("/used-by/<model_id>")
def used_by(model_id: str):
    """Products whose Analytics Model is ``model_id`` (lineage)."""
    return jsonify([p for p in list_products() if p["data"].get("analytics_model") == model_id])


@product_bp.get("/<product_id>")
def get_one(product_id: str):
    product = get_product(product_id)
    if product is None:
        return jsonify({"error": "Product not found"}), 404
    return jsonify(product)


@product_bp.post("")
def register():
    body = json_body()
    # Phase MRC-5: Company is no longer a per-model field. Every instance is
    # a single institution and every model lives under it, so the analytics
    # binding check reduces to "does the model exist".
    dispatch(
        "register_product", register_product, context=context_from_request(body),
        product_id=body.get("product_id"), product=body.get("product"), fields=body.get("fields") or {})
    rebuild_product_view()
    return jsonify(get_product(body.get("product_id"))), 201


@product_bp.post("/<product_id>/field")
def update_field(product_id: str):
    body = json_body()
    dispatch(
        "update_product_field", update_product_field, context=context_from_request(body),
        product_id=product_id, field=body.get("field"), value=body.get("value"))
    rebuild_product_view()
    return jsonify(get_product(product_id))


@product_bp.post("/<product_id>/rebind")
def rebind(product_id: str):
    body = json_body()
    dispatch(
        "rebind_component", rebind_component, context=context_from_request(body),
        product_id=product_id, component=body.get("component"), value=body.get("value"))
    rebuild_product_view()
    return jsonify(get_product(product_id))


@product_bp.post("/<product_id>/retire")
def retire(product_id: str):
    body = json_body()
    dispatch("retire_product", retire_product, context=context_from_request(body), product_id=product_id)
    rebuild_product_view()
    return jsonify(get_product(product_id))


@product_bp.post("/<product_id>/collections/<collection>")
def add_item(product_id: str, collection: str):
    body = json_body()
    dispatch(
        "add_collection_item", add_collection_item, context=context_from_request(body),
        product_id=product_id, collection=collection, fields=body.get("fields") or {})
    rebuild_product_view()
    return jsonify(get_product(product_id)), 201


@product_bp.post("/<product_id>/collections/<collection>/<item_id>")
def update_item(product_id: str, collection: str, item_id: str):
    body = json_body()
    dispatch(
        "update_collection_item", update_collection_item, context=context_from_request(body),
        product_id=product_id, collection=collection, item_id=item_id, fields=body.get("fields") or {})
    rebuild_product_view()
    return jsonify(get_product(product_id))


@product_bp.post("/<product_id>/collections/<collection>/<item_id>/delete")
def delete_item(product_id: str, collection: str, item_id: str):
    body = json_body()
    dispatch(
        "remove_collection_item", remove_collection_item, context=context_from_request(body),
        product_id=product_id, collection=collection, item_id=item_id)
    rebuild_product_view()
    return jsonify(get_product(product_id))


@product_bp.post("/<product_id>/documents")
def upload_document(product_id: str):
    """Supporting Documentation: upload a categorised file against the Product."""
    if get_product(product_id) is None:
        return jsonify({"error": "Product not found"}), 404
    category = request.form.get("category")
    if category not in DOC_CATEGORIES:
        return jsonify({"error": "invalid category"}), 400
    file = request.files.get("file")
    if file is None:
        return jsonify({"error": "no file provided"}), 400
    try:
        add_document(
            aggregate_type=PRODUCT_AGGREGATE, aggregate_id=product_id, scope=_product_scope(product_id),
            category=category, filename=file.filename, data=file.read(),
            description=request.form.get("description", ""), actor=request_actor())
    except UploadError as exc:
        return jsonify({"error": str(exc)}), 400
    rebuild_product_view()
    return jsonify(get_product(product_id)), 201


@product_bp.get("/<product_id>/documents/<item_id>/download")
def download_document(product_id: str, item_id: str):
    doc = find_document(PRODUCT_AGGREGATE, product_id, item_id)
    if doc is None:
        return jsonify({"error": "document not found"}), 404
    path = upload_path(_product_scope(product_id), doc["filename"])
    if not path.exists():
        return jsonify({"error": "file missing"}), 404
    return send_document(path, doc, inline=request.args.get("inline") == "1")


@product_bp.post("/<product_id>/documents/<item_id>/delete")
def delete_document(product_id: str, item_id: str):
    remove_document(
        aggregate_type=PRODUCT_AGGREGATE, aggregate_id=product_id, item_id=item_id, actor=request_actor())
    rebuild_product_view()
    return jsonify(get_product(product_id))
