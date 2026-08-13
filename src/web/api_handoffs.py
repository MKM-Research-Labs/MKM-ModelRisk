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
"""HTTP API for model-to-model handoffs — field lineage on a chain edge.

A handoff hangs off a declared dependency edge. The UI opens one from the Model
Chain screen: ``POST /api/handoffs`` declares it (or returns the existing one),
then the field-lineage and prose are edited through the usual collection/field
routes. Declaring on an edge that is not in the chain is a 400 (the domain guard).
"""
from __future__ import annotations

from datetime import date

from flask import Blueprint, Response, jsonify

from src.command import dispatch
from src.governance.model_handoff import (
    add_collection_item,
    declare_handoff,
    derive_status,
    get_handoff,
    get_handoff_for_edge,
    list_handoffs,
    rebuild_handoff_view,
    remove_collection_item,
    update_collection_item,
    update_handoff_field,
)
from src.governance.model_handoff.document import render_handover_pdf
from src.governance.model_inventory import get_model
from src.governance.mrc import matching_mrc
from src.governance.mrc.pack import TectonicNotFound
from src.governance.reference import get_reference_lists
from src.web._helpers import context_from_request, json_body
from src.web._signoff_routing import HANDOFF_SUBJECT, raise_signoff

handoffs_bp = Blueprint("handoffs", __name__, url_prefix="/api/handoffs")

# The owner edits only the prose. The sign-off stamp and review date are set by
# the committee through the sign-off flow, never this route — so a handoff cannot
# be marked approved by editing it directly.
OWNER_FIELDS = ("data_handoff", "compatibility")


def _decorate(handoff: dict) -> dict:
    """Add the derived status to a handoff document (read-side only). Callers only
    ever pass a handoff that exists (a missing one is a 404 before this point).

    ``derive_status`` lives on the read model rather than here so the neighbourhood
    graph, which labels the same edge, cannot drift from this."""
    handoff["data"]["status"] = derive_status(handoff["data"] or {})
    return handoff


@handoffs_bp.get("")
def list_all():
    return jsonify([_decorate(h) for h in list_handoffs()])


@handoffs_bp.post("")
def declare():
    """Declare the handoff on an edge, or return it if already declared."""
    body = json_body()
    from_model, to_model = body.get("from_model"), body.get("to_model")
    existing = get_handoff_for_edge(from_model, to_model)
    if existing is not None:
        return jsonify(_decorate(existing)), 200
    dispatch("declare_handoff", declare_handoff, context=context_from_request(body),
             from_model=from_model, to_model=to_model)
    rebuild_handoff_view()
    return jsonify(_decorate(get_handoff_for_edge(from_model, to_model))), 201


@handoffs_bp.get("/<hid>")
def get_one(hid: str):
    handoff = get_handoff(hid)
    if handoff is None:
        return jsonify({"error": "handoff not found"}), 404
    return jsonify(_decorate(handoff))


@handoffs_bp.get("/<hid>/handover.pdf")
def handover_document(hid: str):
    """The Model Interoperability Validation document for this handoff, as a PDF."""
    handoff = get_handoff(hid)
    if handoff is None:
        return jsonify({"error": "handoff not found"}), 404
    data = handoff["data"] or {}
    provider = get_model(data.get("from_model"))
    consumer = get_model(data.get("to_model"))
    try:
        pdf = render_handover_pdf(handoff, provider, consumer, date.today().isoformat())
    except TectonicNotFound as exc:
        return jsonify({"error": str(exc)}), 503
    return Response(pdf, mimetype="application/pdf", headers={
        "Content-Disposition": f'inline; filename="handover_{hid}.pdf"',
    })


@handoffs_bp.post("/<hid>/field")
def update_field(hid: str):
    body = json_body()
    field = body.get("field")
    if field not in OWNER_FIELDS:
        return jsonify({"error": f"field not editable: {field}"}), 400
    dispatch("update_handoff_field", update_handoff_field, context=context_from_request(body),
             handoff_id=hid, field=field, value=body.get("value"))
    rebuild_handoff_view()
    return jsonify(_decorate(get_handoff(hid)))


@handoffs_bp.post("/<hid>/request-signoff")
def request_signoff(hid: str):
    """The owner asks the MRC to ratify this handoff's compatibility. It is routed
    to the committee responsible for the *consumer* model (the one relying on the
    handoff) and queued; attached immediately if a meeting of that MRC is scheduled."""
    handoff = get_handoff(hid)
    if handoff is None:
        return jsonify({"error": "handoff not found"}), 404
    # The edge constraint guarantees the consumer was a registered model when the
    # handoff was declared, and retiring never removes it from the inventory — so
    # get_model here always resolves.
    consumer = get_model((handoff["data"] or {}).get("to_model"))
    data = consumer["data"] or {}
    mrc, _level = matching_mrc(data.get("division"), data.get("line_of_business"), get_reference_lists())
    if mrc is None:
        return jsonify({"error": "no MRC committee covers the consumer model's "
                                 "division / line of business — configure one under Admin → MRC first"}), 400
    body = json_body()
    raise_signoff(context_from_request(body), HANDOFF_SUBJECT, hid,
                  kind="handoff", target_mrc=mrc["value"], note=body.get("note"))
    return jsonify(_decorate(get_handoff(hid))), 201


@handoffs_bp.post("/<hid>/collections/<collection>")
def add_item(hid: str, collection: str):
    body = json_body()
    dispatch("add_collection_item", add_collection_item, context=context_from_request(body),
             handoff_id=hid, collection=collection, fields=body.get("fields") or {})
    rebuild_handoff_view()
    return jsonify(_decorate(get_handoff(hid))), 201


@handoffs_bp.post("/<hid>/collections/<collection>/<item_id>")
def update_item(hid: str, collection: str, item_id: str):
    body = json_body()
    dispatch("update_collection_item", update_collection_item, context=context_from_request(body),
             handoff_id=hid, collection=collection, item_id=item_id, fields=body.get("fields") or {})
    rebuild_handoff_view()
    return jsonify(_decorate(get_handoff(hid)))


@handoffs_bp.post("/<hid>/collections/<collection>/<item_id>/delete")
def delete_item(hid: str, collection: str, item_id: str):
    body = json_body()
    dispatch("remove_collection_item", remove_collection_item, context=context_from_request(body),
             handoff_id=hid, collection=collection, item_id=item_id)
    rebuild_handoff_view()
    return jsonify(_decorate(get_handoff(hid)))
