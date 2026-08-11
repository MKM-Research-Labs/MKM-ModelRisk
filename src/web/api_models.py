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
"""HTTP API for the model-inventory aggregate."""
from __future__ import annotations

from datetime import date

from flask import Blueprint, jsonify, request

from config.governance import (COLLECTION_SPECS, DOC_CATEGORIES, MODEL_FIELD_SPECS,
                               REGISTER_FIELDS, VALID_REVIEW_TRIGGERS)
from src.files import UploadError, upload_path
from src.governance.documents import (add_document, find_document, model_scope,
                                      remove_document)
from src.governance.model_handoff import annotate_links, annotate_neighbourhood
from src.governance.model_inventory.commands import AGGREGATE_TYPE as MODEL_AGGREGATE
from src.governance.model_inventory.risk import compute_risk_rating
from src.governance.mrc import meeting_items_for_model
from src.command import dispatch
from src.governance.model_inventory import (
    add_collection_item,
    derive_chain,
    derive_neighbourhood,
    get_model,
    list_models,
    rebuild_inventory_view,
    register_model,
    remove_collection_item,
    update_collection_item,
    update_model_field,
)
from src.web._owner_ratification import set_model_field
from src.web._helpers import (
    context_from_request,
    json_body,
    reference_options,
    request_actor,
    resolve_field,
    document_specs,
    resolve_mrc_for_org,
    send_document,
)


models_bp = Blueprint("models", __name__, url_prefix="/api/models")


def _grouped_specs(options_by_list: dict[str, list]):
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
        resolved = resolve_field({**spec, "key": key}, options_by_list)
        field = {"key": resolved["key"], "label": resolved["label"],
                 "type": resolved["type"], "options": resolved["options"]}
        # What each option is shown as, where a status vocabulary separates the word
        # a record stores from the word a screen shows. Carried only when the two
        # differ, so every other field's payload is unchanged.
        if resolved.get("option_labels"):
            field["option_labels"] = resolved["option_labels"]
        group["fields"].append(field)
    return groups


def _collection_specs():
    """Collection metadata (label, id prefix, item fields) for the UI."""
    options_by_list = reference_options()
    return [
        {
            "key": key, "label": spec["label"], "id_prefix": spec["id_prefix"],
            "fields": [resolve_field(f, options_by_list) for f in spec["fields"]],
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
        # Why a review is being run. The server validates against this list, so the
        # console has to offer the same one — served rather than copied, or the two
        # drift and a legitimate trigger starts being refused.
        "review_triggers": list(VALID_REVIEW_TRIGGERS),
        **document_specs(),
    })


@models_bp.get("/<model_id>/mrc")
def model_mrc(model_id: str):
    """The MRC committee responsible for this model, derived from its org unit."""
    model = get_model(model_id)
    if model is None:
        return jsonify({"error": "model not found"}), 404
    data = model["data"] or {}
    return jsonify(resolve_mrc_for_org(data.get("division"), data.get("line_of_business")))


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
            aggregate_type=MODEL_AGGREGATE, aggregate_id=model_id, scope=model_scope(model_id),
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
    path = upload_path(model_scope(model_id), doc["filename"])
    if not path.exists():
        return jsonify({"error": "file missing"}), 404
    return send_document(path, doc, inline=request.args.get("inline") == "1")


@models_bp.post("/<model_id>/documents/<item_id>/delete")
def delete_document(model_id: str, item_id: str):
    remove_document(
        aggregate_type=MODEL_AGGREGATE, aggregate_id=model_id, item_id=item_id, actor=request_actor(),
    )
    rebuild_inventory_view()
    return jsonify(get_model(model_id))


@models_bp.get("")
def list_all():
    """The live inventory. ``?include_retired=1`` adds the hibernated models back —
    the console asks for them only when somebody goes looking for one to reactivate,
    so a retired model is not in the list, the tiles or any figure drawn from them."""
    include_retired = request.args.get("include_retired") == "1"
    return jsonify(list_models(include_retired=include_retired))


@models_bp.get("/<model_id>/neighbourhood")
def model_neighbourhood(model_id: str):
    """One model's neighbourhood — feeds, shared-source siblings, terminal flag."""
    result = derive_neighbourhood(model_id)
    if result is None:
        return jsonify({"error": "model not found"}), 404
    return jsonify(annotate_neighbourhood(result))


@models_bp.get("/chain")
def model_chain():
    """The 'string of pearls' derived from every model's declared dependencies."""
    chain = derive_chain()
    annotate_links(chain["links"])
    return jsonify(chain)


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
    payload = compute_risk_rating(model["data"], as_of=date.today().isoformat())
    from src.web.api_models_signoff import pending_signoff  # avoids import cycle
    payload["pending_signoff"] = pending_signoff(model_id)
    return jsonify(payload)


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


@models_bp.get("/<model_id>/analysis-presentations")
def analysis_presentations_for_model(model_id: str):
    """Read-only: every meeting where this model was in scope for analysis — i.e.
    where its analysis was presented to an MRC, with the outcome and any paper."""
    if get_model(model_id) is None:
        return jsonify({"error": "model not found"}), 404
    return jsonify(meeting_items_for_model("models_in_scope", model_id))


@models_bp.post("")
def register():
    body = json_body()
    # Every instance is a single institution — company is no longer a per-
    # model field (see Phase MRC-5). All models sit under the institution.
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
    # An owner change carries a committee ratification with it (see
    # _owner_ratification): the write is the same, what follows it is not.
    set_model_field(context_from_request(body), model_id,
                    field=body.get("field"), value=body.get("value"))
    return jsonify(get_model(model_id))


# Retiring a model is not something an owner does directly any more: it is
# hibernation, and it takes MRC ratification. The owner raises a request
# (POST /<model_id>/request-retire in api_models_signoff) and the committee
# carries it out on approval, which is the only path that appends ModelRetired.


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
