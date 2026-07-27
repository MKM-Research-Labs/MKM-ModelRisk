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
"""HTTP API for the Client aggregate."""
from __future__ import annotations

from datetime import date, datetime

from flask import Blueprint, Response, jsonify, request

from config.governance import (
    CLIENT_COLLECTION_SPECS,
    CLIENT_FIELD_SPECS,
    CLIENT_PACKS,
    CLIENT_REGISTER_FIELDS,
)
from src.command import dispatch
from src.files import UploadError, store_generated, upload_path
from src.governance.client import (
    add_collection_item,
    build_client_pack,
    get_client,
    list_clients,
    pack_manifest,
    rebuild_client_view,
    record_client_pack,
    register_client,
    remove_collection_item,
    retire_client,
    update_client_field,
    update_collection_item,
)
from src.governance.client.commands import AGGREGATE_TYPE as CLIENT_AGGREGATE
from src.governance.documents import add_document, client_scope, find_document, remove_document
from src.governance.model_inventory import list_models
from src.governance.mrc.pack import TectonicNotFound
from src.governance.mrc_settings import get_settings
from src.governance.product import list_products
from src.web._helpers import (
    context_from_request,
    json_body,
    reference_options,
    request_actor,
    resolve_field,
    send_document,
)

_PACK_SCOPE = "client_pack/{client_id}"
_SUPPLEMENTARY_CATEGORY = "Supplementary"

client_bp = Blueprint("client", __name__, url_prefix="/api/clients")


def _grouped_specs(options: dict[str, list]):
    """Field specs grouped for the detail view; references resolve to dropdowns."""
    groups: list[dict] = []
    by_name: dict[str, dict] = {}
    for key, spec in CLIENT_FIELD_SPECS.items():
        group = by_name.get(spec["group"])
        if group is None:
            group = {"group": spec["group"], "fields": []}
            by_name[spec["group"]] = group
            groups.append(group)
        field_type, choices = spec["type"], list(spec.get("options", []))
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
        for key, spec in CLIENT_COLLECTION_SPECS.items()
    ]


@client_bp.get("/fields")
def field_specs():
    """Field and collection specs plus the register-form minimum."""
    return jsonify({
        "groups": _grouped_specs(reference_options()),
        "register": list(CLIENT_REGISTER_FIELDS),
        "collections": _collection_specs(),
    })


@client_bp.get("")
def list_all():
    return jsonify(list_clients())


@client_bp.get("/<client_id>")
def get_one(client_id: str):
    client = get_client(client_id)
    if client is None:
        return jsonify({"error": "Client not found"}), 404
    return jsonify(client)


@client_bp.get("/<client_id>/link-options")
def link_options(client_id: str):
    """Live Products and Models a client may be linked to (dropdown sources)."""
    return jsonify({
        "products": [{"id": p["product_id"], "label": (p["data"] or {}).get("product") or p["product_id"]}
                     for p in list_products() if not p["retired"]],
        "models": [{"id": m["model_id"], "label": (m["data"] or {}).get("name") or m["model_id"]}
                   for m in list_models() if not m["retired"]],
    })


@client_bp.post("")
def register():
    body = json_body()
    event = dispatch(
        "register_client", register_client, context=context_from_request(body),
        name=body.get("name"), fields=body.get("fields") or {})
    rebuild_client_view()
    return jsonify(get_client(event.aggregate_id)), 201


@client_bp.post("/<client_id>/field")
def update_field(client_id: str):
    body = json_body()
    dispatch(
        "update_client_field", update_client_field, context=context_from_request(body),
        client_id=client_id, field=body.get("field"), value=body.get("value"))
    rebuild_client_view()
    return jsonify(get_client(client_id))


@client_bp.post("/<client_id>/retire")
def retire(client_id: str):
    body = json_body()
    dispatch("retire_client", retire_client, context=context_from_request(body), client_id=client_id)
    rebuild_client_view()
    return jsonify(get_client(client_id))


@client_bp.post("/<client_id>/collections/<collection>")
def add_item(client_id: str, collection: str):
    body = json_body()
    dispatch(
        "add_collection_item", add_collection_item, context=context_from_request(body),
        client_id=client_id, collection=collection, fields=body.get("fields") or {})
    rebuild_client_view()
    return jsonify(get_client(client_id)), 201


@client_bp.post("/<client_id>/collections/<collection>/<item_id>")
def update_item(client_id: str, collection: str, item_id: str):
    body = json_body()
    dispatch(
        "update_collection_item", update_collection_item, context=context_from_request(body),
        client_id=client_id, collection=collection, item_id=item_id, fields=body.get("fields") or {})
    rebuild_client_view()
    return jsonify(get_client(client_id))


@client_bp.post("/<client_id>/collections/<collection>/<item_id>/delete")
def delete_item(client_id: str, collection: str, item_id: str):
    body = json_body()
    dispatch(
        "remove_collection_item", remove_collection_item, context=context_from_request(body),
        client_id=client_id, collection=collection, item_id=item_id)
    rebuild_client_view()
    return jsonify(get_client(client_id))


def _zip_response(data: bytes, filename: str) -> Response:
    return Response(data, mimetype="application/zip", headers={
        "Content-Disposition": f'attachment; filename="{filename}"',
    })


@client_bp.get("/<client_id>/pack/preview")
def pack_preview(client_id: str):
    """A manifest of what a pack would contain — the preview step before committing.

    Computed without compiling any PDF, so it returns instantly; it mirrors the
    generate step's source selection and surfaces the same warnings up front."""
    client = get_client(client_id)
    if client is None:
        return jsonify({"error": "Client not found"}), 404
    return jsonify(pack_manifest(client, get_settings()))


@client_bp.post("/<client_id>/pack")
def generate_pack(client_id: str):
    """Build the pack, retain the timestamped ZIP, and record a history row.

    Bi-temporal: ``as_of`` is today's valid time; ``generated_at`` is the
    transaction time. Both are server-stamped onto the retained file and its row.
    """
    body = json_body()
    client = get_client(client_id)
    if client is None:
        return jsonify({"error": "Client not found"}), 404
    now = datetime.now()
    as_of = date.today().isoformat()
    generated_at = now.isoformat(timespec="seconds")
    try:
        data = build_client_pack(client, get_settings(), as_of, generated_at)
    except TectonicNotFound as exc:
        return jsonify({"error": str(exc)}), 503
    stamp = now.strftime("%Y%m%dT%H%M%S")
    original = f"{(client['data'] or {}).get('name') or client_id}_client_pack_{as_of}.zip"
    meta = store_generated(_PACK_SCOPE.format(client_id=client_id),
                           f"{client_id}_client_pack_{stamp}.zip", data)
    dispatch(
        "record_client_pack", record_client_pack, context=context_from_request(body),
        client_id=client_id, as_of=as_of, generated_at=generated_at,
        filename=meta["filename"], original_name=original, size=len(data))
    rebuild_client_view()
    return jsonify(get_client(client_id)), 201


@client_bp.get("/<client_id>/packs/<item_id>.zip")
def download_pack(client_id: str, item_id: str):
    """Download a previously generated, retained pack from the client's history."""
    client = get_client(client_id)
    if client is None:
        return jsonify({"error": "Client not found"}), 404
    row = next((p for p in (client["data"] or {}).get(CLIENT_PACKS, [])
                if p.get("item_id") == item_id), None)
    if row is None:
        return jsonify({"error": "pack not found"}), 404
    path = upload_path(_PACK_SCOPE.format(client_id=client_id), row["filename"])
    if not path.exists():
        return jsonify({"error": "pack file missing"}), 404
    return _zip_response(path.read_bytes(), row.get("original_name") or row["filename"])


@client_bp.post("/<client_id>/documents")
def upload_document(client_id: str):
    """Attach a supplementary document to the client; it is bundled into the pack."""
    if get_client(client_id) is None:
        return jsonify({"error": "Client not found"}), 404
    file = request.files.get("file")
    if file is None:
        return jsonify({"error": "no file provided"}), 400
    try:
        add_document(
            aggregate_type=CLIENT_AGGREGATE, aggregate_id=client_id,
            scope=client_scope(client_id), category=_SUPPLEMENTARY_CATEGORY,
            filename=file.filename, data=file.read(),
            description=request.form.get("description", ""), actor=request_actor())
    except UploadError as exc:
        return jsonify({"error": str(exc)}), 400
    rebuild_client_view()
    return jsonify(get_client(client_id)), 201


@client_bp.get("/<client_id>/documents/<item_id>/download")
def download_document(client_id: str, item_id: str):
    doc = find_document(CLIENT_AGGREGATE, client_id, item_id)
    if doc is None:
        return jsonify({"error": "document not found"}), 404
    path = upload_path(client_scope(client_id), doc["filename"])
    if not path.exists():
        return jsonify({"error": "file missing"}), 404
    return send_document(path, doc, inline=request.args.get("inline") == "1")


@client_bp.post("/<client_id>/documents/<item_id>/delete")
def delete_document(client_id: str, item_id: str):
    if find_document(CLIENT_AGGREGATE, client_id, item_id) is None:
        return jsonify({"error": "document not found"}), 404
    remove_document(aggregate_type=CLIENT_AGGREGATE, aggregate_id=client_id,
                    item_id=item_id, actor=request_actor())
    rebuild_client_view()
    return jsonify(get_client(client_id))
