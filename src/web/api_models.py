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
"""HTTP API for the model-inventory aggregate."""
from __future__ import annotations

from datetime import date

from flask import Blueprint, Response, jsonify, request, send_file

from config.governance import COLLECTION_SPECS, DOC_CATEGORIES, MODEL_FIELD_SPECS, REGISTER_FIELDS
from src.files import UploadError, upload_path
from src.governance.documents import add_document, find_document, remove_document
from src.governance.model_inventory.commands import AGGREGATE_TYPE as MODEL_AGGREGATE
from src.governance.model_inventory.report import render_report_pdf
from src.governance.model_inventory.risk import compute_risk_rating
from src.governance.mrc import meeting_items_for_model
from src.governance.mrc_settings import get_settings
from src.command import dispatch
from src.governance.model_inventory import (
    add_collection_item,
    get_model,
    list_models,
    rebuild_inventory_view,
    register_model,
    remove_collection_item,
    retire_model,
    update_collection_item,
    update_model_field,
)
from src.web._helpers import context_from_request, json_body, reference_options, request_actor


def _model_scope(model_id: str) -> str:
    return f"model/{model_id}"

models_bp = Blueprint("models", __name__, url_prefix="/api/models")


def _grouped_specs(reference_options: dict[str, list]):
    """Field specs grouped for the detail view.

    Fields backed by a reference list become dropdowns (type ``choice``) once
    that admin-managed list has values; otherwise they stay free text.
    """
    groups: list[dict] = []
    by_name: dict[str, dict] = {}
    for key, spec in MODEL_FIELD_SPECS.items():
        group = by_name.get(spec["group"])
        if group is None:
            group = {"group": spec["group"], "fields": []}
            by_name[spec["group"]] = group
            groups.append(group)
        field_type = spec["type"]
        options = list(spec.get("options", []))
        reference = spec.get("reference")
        if reference and reference_options.get(reference):
            field_type = "choice"
            options = reference_options[reference]
        group["fields"].append(
            {"key": key, "label": spec["label"], "type": field_type, "options": options}
        )
    return groups


def _collection_specs():
    """Collection metadata (label, id prefix, item fields) for the UI."""
    return [
        {
            "key": key,
            "label": spec["label"],
            "id_prefix": spec["id_prefix"],
            "fields": [
                {
                    "key": f["key"],
                    "label": f["label"],
                    "type": f["type"],
                    "options": list(f.get("options", [])),
                    "required": bool(f.get("required")),
                }
                for f in spec["fields"]
            ],
        }
        for key, spec in COLLECTION_SPECS.items()
    ]


@models_bp.get("/fields")
def field_specs():
    """Field metadata so the UI can render the form and editors generically."""
    return jsonify({
        "groups": _grouped_specs(reference_options()),
        "register": list(REGISTER_FIELDS),
        "collections": _collection_specs(),
        "doc_categories": list(DOC_CATEGORIES),
    })


@models_bp.post("/<model_id>/documents")
def upload_document(model_id: str):
    if get_model(model_id) is None:
        return jsonify({"error": "model not found"}), 404
    category = request.form.get("category")
    if category not in DOC_CATEGORIES:
        return jsonify({"error": "invalid category"}), 400
    file = request.files.get("file")
    if file is None:
        return jsonify({"error": "no file provided"}), 400
    try:
        add_document(
            aggregate_type=MODEL_AGGREGATE, aggregate_id=model_id, scope=_model_scope(model_id),
            category=category, filename=file.filename, data=file.read(),
            description=request.form.get("description", ""), actor=request_actor(),
        )
    except UploadError as exc:
        return jsonify({"error": str(exc)}), 400
    rebuild_inventory_view()
    return jsonify(get_model(model_id)), 201


@models_bp.get("/<model_id>/documents/<item_id>/download")
def download_document(model_id: str, item_id: str):
    doc = find_document(MODEL_AGGREGATE, model_id, item_id)
    if doc is None:
        return jsonify({"error": "document not found"}), 404
    path = upload_path(_model_scope(model_id), doc["filename"])
    if not path.exists():
        return jsonify({"error": "file missing"}), 404
    return send_file(str(path), as_attachment=True, download_name=doc["original_name"])


@models_bp.post("/<model_id>/documents/<item_id>/delete")
def delete_document(model_id: str, item_id: str):
    remove_document(
        aggregate_type=MODEL_AGGREGATE, aggregate_id=model_id, item_id=item_id, actor=request_actor(),
    )
    rebuild_inventory_view()
    return jsonify(get_model(model_id))


@models_bp.get("")
def list_all():
    return jsonify(list_models())


@models_bp.get("/risk-report.pdf")
def risk_report():
    """The Model Risk Report (MRC status) as a LaTeX-generated PDF."""
    pdf = render_report_pdf(list_models(), get_settings(), date.today().isoformat())
    return Response(pdf, mimetype="application/pdf", headers={
        "Content-Disposition": 'inline; filename="model_risk_report.pdf"',
    })


@models_bp.get("/<model_id>")
def get_one(model_id: str):
    model = get_model(model_id)
    if model is None:
        return jsonify({"error": "model not found"}), 404
    return jsonify(model)


@models_bp.get("/<model_id>/risk-rating")
def risk_rating(model_id: str):
    model = get_model(model_id)
    if model is None:
        return jsonify({"error": "model not found"}), 404
    return jsonify(compute_risk_rating(model["data"], as_of=date.today().isoformat()))


@models_bp.get("/<model_id>/decisions")
def decisions_for_model(model_id: str):
    """Read-only: every MRC decision linked to this model."""
    if get_model(model_id) is None:
        return jsonify({"error": "model not found"}), 404
    return jsonify(meeting_items_for_model("decisions", model_id))


@models_bp.get("/<model_id>/actions")
def actions_for_model(model_id: str):
    """Read-only: every MRC action linked to this model."""
    if get_model(model_id) is None:
        return jsonify({"error": "model not found"}), 404
    return jsonify(meeting_items_for_model("actions", model_id))


@models_bp.post("")
def register():
    body = json_body()
    dispatch(
        "register_model", register_model, context=context_from_request(body),
        model_id=body.get("model_id"), name=body.get("name"),
        fields=body.get("fields") or {},
    )
    rebuild_inventory_view()
    return jsonify(get_model(body.get("model_id"))), 201


@models_bp.post("/<model_id>/field")
def update_field(model_id: str):
    body = json_body()
    dispatch(
        "update_model_field", update_model_field, context=context_from_request(body),
        model_id=model_id, field=body.get("field"), value=body.get("value"),
    )
    rebuild_inventory_view()
    return jsonify(get_model(model_id))


@models_bp.post("/<model_id>/retire")
def retire(model_id: str):
    body = json_body()
    dispatch(
        "retire_model", retire_model, context=context_from_request(body),
        model_id=model_id,
    )
    rebuild_inventory_view()
    return jsonify(get_model(model_id))


@models_bp.post("/<model_id>/collections/<collection>")
def add_item(model_id: str, collection: str):
    body = json_body()
    dispatch(
        "add_collection_item", add_collection_item, context=context_from_request(body),
        model_id=model_id, collection=collection, fields=body.get("fields") or {},
    )
    rebuild_inventory_view()
    return jsonify(get_model(model_id)), 201


@models_bp.post("/<model_id>/collections/<collection>/<item_id>")
def update_item(model_id: str, collection: str, item_id: str):
    body = json_body()
    dispatch(
        "update_collection_item", update_collection_item, context=context_from_request(body),
        model_id=model_id, collection=collection, item_id=item_id,
        fields=body.get("fields") or {},
    )
    rebuild_inventory_view()
    return jsonify(get_model(model_id))


@models_bp.post("/<model_id>/collections/<collection>/<item_id>/delete")
def delete_item(model_id: str, collection: str, item_id: str):
    body = json_body()
    dispatch(
        "remove_collection_item", remove_collection_item, context=context_from_request(body),
        model_id=model_id, collection=collection, item_id=item_id,
    )
    rebuild_inventory_view()
    return jsonify(get_model(model_id))
