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
"""HTTP API for the AI System aggregate.

Deliberately thinner than the ML Application's: no training endpoints, because
nobody in the firm fitted this, and no version dropdown, because the versions worth
naming are the provider's rather than a menu we maintain.
"""
from __future__ import annotations

from datetime import date

from flask import Blueprint, jsonify, request

from config.governance._ai_system import (AI_SYSTEM_COLLECTION_SPECS,
                                          AI_SYSTEM_FIELD_SPECS,
                                          AI_SYSTEM_REGISTER_FIELDS)
from src.command import dispatch
from src.governance.ai_system import (add_collection_item, get_ai_system,
                                      list_ai_systems, rebuild_ai_system_view,
                                      register_ai_system, remove_collection_item,
                                      update_ai_system_field, update_collection_item)
from src.governance.model_inventory.risk import compute_risk_rating
from config.governance._ai_regimes import regimes_for
from config.governance._ai_triggers import FALLBACK_STATES, TRIGGER_PROPERTIES
from config.governance._change import CHANGE_CLASSES
from src.governance.ai_system._rules import diff_snapshots
from src.governance.ai_system.envelope import envelope_status
from src.governance.ai_system import (current_config_version,
                                      latest_envelope,
                                      list_snapshots,
                                      rebuild_configuration_snapshot_view,
                                      take_configuration_snapshot)
from src.web._review_stages import review_specs
from src.web._signoff_subject import AI_SYSTEM_SUBJECT
from src.web._helpers import (collection_field_specs, context_from_request,
                              document_specs, grouped_field_specs, json_body,
                              reference_options, resolve_mrc_for_record)

ai_system_bp = Blueprint("ai_system", __name__, url_prefix="/api/ai-systems")


@ai_system_bp.get("/fields")
def field_specs():
    """The record's shape, for the register form and the detail screen.

    Served rather than duplicated in JavaScript, for the reason every other record
    type serves it: the screens, the completeness score and the generated documents
    all read one table, so a field added in config reaches all three at once.
    """
    return jsonify({
        "groups": grouped_field_specs(AI_SYSTEM_FIELD_SPECS, reference_options()),
        "register": list(AI_SYSTEM_REGISTER_FIELDS),
        "collections": collection_field_specs(AI_SYSTEM_COLLECTION_SPECS),
        **document_specs(),
        **review_specs(AI_SYSTEM_SUBJECT),
        # The vocabularies the operate controls offer. Served for the same reason as
        # everything above: a console holding its own copy offers an adopter's renamed
        # fallback under the old name, or a property the command then refuses.
        "trigger_properties": list(TRIGGER_PROPERTIES),
        "fallback_states": list(FALLBACK_STATES),
        "change_classes": list(CHANGE_CLASSES),
    })


@ai_system_bp.get("")
def list_all():
    """The live AI Systems. ``?include_retired=1`` adds the hibernated ones back."""
    include_retired = request.args.get("include_retired") == "1"
    return jsonify(list_ai_systems(include_retired=include_retired))


@ai_system_bp.get("/<ai_system_id>")
def get_one(ai_system_id: str):
    record = get_ai_system(ai_system_id)
    if record is None:
        return jsonify({"error": "AI System not found"}), 404
    return jsonify(record)


@ai_system_bp.post("")
def register():
    body = json_body()
    ai_system_id = body.get("ai_system_id")
    dispatch("register_ai_system", register_ai_system,
             context=context_from_request(body), ai_system_id=ai_system_id,
             fields=body.get("fields") or {})
    rebuild_ai_system_view()
    return jsonify(get_ai_system(ai_system_id)), 201


@ai_system_bp.post("/<ai_system_id>/field")
def update_field(ai_system_id: str):
    body = json_body()
    dispatch("update_ai_system_field", update_ai_system_field,
             context=context_from_request(body), ai_system_id=ai_system_id,
             field=body.get("field"), value=body.get("value"))
    rebuild_ai_system_view()
    return jsonify(get_ai_system(ai_system_id))


# There is no retire endpoint here, and that absence is the design. Retiring is
# hibernation and the committee's decision: the owner raises it at
# POST /<ai_system_id>/request-retire (api_ai_system_signoff) and the MRC ratifies
# it, which is where retire_ai_system is finally dispatched. A route here would be
# a second way to the same event, and the un-gated one.


@ai_system_bp.post("/<ai_system_id>/collections/<collection>")
def add_item(ai_system_id: str, collection: str):
    body = json_body()
    dispatch("add_collection_item", add_collection_item,
             context=context_from_request(body), ai_system_id=ai_system_id,
             collection=collection, fields=body.get("fields") or {})
    rebuild_ai_system_view()
    return jsonify(get_ai_system(ai_system_id)), 201


@ai_system_bp.post("/<ai_system_id>/collections/<collection>/<item_id>")
def update_item(ai_system_id: str, collection: str, item_id: str):
    body = json_body()
    dispatch("update_collection_item", update_collection_item,
             context=context_from_request(body), ai_system_id=ai_system_id,
             collection=collection, item_id=item_id, fields=body.get("fields") or {})
    rebuild_ai_system_view()
    return jsonify(get_ai_system(ai_system_id))


@ai_system_bp.post("/<ai_system_id>/collections/<collection>/<item_id>/delete")
def delete_item(ai_system_id: str, collection: str, item_id: str):
    body = json_body()
    dispatch("remove_collection_item", remove_collection_item,
             context=context_from_request(body), ai_system_id=ai_system_id,
             collection=collection, item_id=item_id)
    rebuild_ai_system_view()
    return jsonify(get_ai_system(ai_system_id))


@ai_system_bp.get("/<ai_system_id>/risk-rating")
def risk_rating(ai_system_id: str):
    """Composite risk rating + heatmap -- the same engine a model, a Product and an
    ML Application use. An AI System carries the same three dimensions and the same
    bands, so it is rated by the same code rather than a second implementation free
    to drift from it."""
    record = get_ai_system(ai_system_id)
    if record is None:
        return jsonify({"error": "AI System not found"}), 404
    return jsonify(compute_risk_rating(record["data"] or {}, as_of=date.today().isoformat()))


@ai_system_bp.get("/<ai_system_id>/snapshots")
def configuration_snapshots(ai_system_id: str):
    """Every configuration this system has run under, oldest first, with what moved.

    The diff travels with each snapshot rather than being a second call: "what changed
    at version 4" is the only question anybody asks of a version list, and making it a
    separate request means a screen that shows the list without it.
    """
    if get_ai_system(ai_system_id) is None:
        return jsonify({"error": "AI System not found"}), 404
    snapshots = list_snapshots(ai_system_id)
    out = []
    for index, row in enumerate(snapshots):
        previous = snapshots[index - 1]["data"] if index else None
        out.append({**row["data"],
                    "changed": diff_snapshots(previous, row["data"]) if previous else []})
    return jsonify({"snapshots": out})


@ai_system_bp.post("/<ai_system_id>/snapshots")
def take_snapshot(ai_system_id: str):
    """Record the configuration as it stands now, as a new immutable version."""
    body = json_body()
    dispatch("take_configuration_snapshot", take_configuration_snapshot,
             context=context_from_request(body), ai_system_id=ai_system_id)
    rebuild_configuration_snapshot_view()
    return jsonify({"snapshots": [r["data"] for r in list_snapshots(ai_system_id)]}), 201


@ai_system_bp.get("/<ai_system_id>/envelope")
def variability_envelope(ai_system_id: str):
    """The measured variability envelope, read against the configuration in force now.

    Staleness is resolved here rather than on the screen: an envelope measured under a
    configuration that has since moved describes a system that no longer exists, and a
    console deciding that for itself would decide it differently from the report.
    """
    if get_ai_system(ai_system_id) is None:
        return jsonify({"error": "AI System not found"}), 404
    envelope = latest_envelope(ai_system_id)
    if envelope is None:
        return jsonify({"envelope": None})
    return jsonify({"envelope": envelope_status(
        envelope, current_config_version(ai_system_id))})


@ai_system_bp.get("/<ai_system_id>/regimes")
def applicable_regimes(ai_system_id: str):
    """Which regulatory regimes apply to this system, and why each one does.

    Derived from the record — where it is used and what it does — rather than ticked.
    "Which regimes apply" has a right answer given those facts, and a checkbox somebody
    ticked is an assertion nobody can check.
    """
    record = get_ai_system(ai_system_id)
    if record is None:
        return jsonify({"error": "AI System not found"}), 404
    return jsonify({"regimes": regimes_for(record.get("data") or {})})


@ai_system_bp.get("/<ai_system_id>/mrc")
def responsible_mrc(ai_system_id: str):
    """The committee responsible for this AI System, resolved from its Division and
    Line of Business the same way a model's is."""
    record = get_ai_system(ai_system_id)
    if record is None:
        return jsonify({"error": "AI System not found"}), 404
    data = record["data"] or {}
    return jsonify(resolve_mrc_for_record("ai_system", data))
