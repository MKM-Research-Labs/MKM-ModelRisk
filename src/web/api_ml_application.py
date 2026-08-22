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
"""HTTP API for the ML Application aggregate."""
from __future__ import annotations

from datetime import date

from flask import Blueprint, jsonify

from config.governance import (ESTIMATOR_LIST, ML_APPLICATION_COLLECTION_SPECS,
                               ML_APPLICATION_FIELD_SPECS, ML_APPLICATION_REGISTER_FIELDS,
                               TRAINING_FIELD_SPECS, TRAINING_RUNS_COLLECTION,
                               TRAINING_SECTIONS)
from config.governance._ml_training import TRAINING_ARTEFACTS
from src.command import dispatch
from src.governance.ml_application import (add_collection_item, get_ml_application,
                                           list_ml_applications,
                                           rebuild_ml_application_view,
                                           register_ml_application, remove_collection_item,
                                           retire_ml_application, update_collection_item,
                                           update_ml_application_field)
from src.governance.model_inventory.risk import compute_risk_rating
from src.governance.reference import get_reference_lists
from src.web._helpers import (collection_field_specs, context_from_request,
                              resolve_mrc_for_org,
                              document_specs, grouped_field_specs, json_body,
                              reference_options, resolve_field)

ml_application_bp = Blueprint("ml_application", __name__, url_prefix="/api/ml-applications")


def _versions_by_estimator() -> dict[str, list[str]]:
    """Which versions each Estimator offers, for the version dropdown.

    The same shape as the Product editor's ``models_by_type``: the form narrows the
    version list once an estimator is chosen, rather than offering every version
    anybody has ever recorded. Parsed from the admin row's comma-separated
    ``versions`` field, so adding a release stays an Admin action.

    An estimator with no versions recorded maps to an empty list, and the form falls
    back to free text -- an institution that has not filled the menu in must still be
    able to state which version it actually ran.
    """
    versions: dict[str, list[str]] = {}
    for row in get_reference_lists().get(ESTIMATOR_LIST) or []:
        recorded = str(row.get("versions") or "")
        versions[str(row.get("value") or "")] = [
            part.strip() for part in recorded.split(",") if part.strip()]
    return versions


@ml_application_bp.get("/fields")
def field_specs():
    return jsonify({
        "groups": grouped_field_specs(ML_APPLICATION_FIELD_SPECS, reference_options()),
        "register": list(ML_APPLICATION_REGISTER_FIELDS),
        "collections": collection_field_specs(ML_APPLICATION_COLLECTION_SPECS),
        "versions_by_estimator": _versions_by_estimator(),
        # The Training tab's structure, from the one place it is declared. The form
        # renders the sections in this order; the
        # completeness count reads the same table, so the page and the score cannot
        # disagree about what is being asked for.
        # Each section carries its fields as an ORDERED list. A dict would be sorted
        # in transit and the order here is the governance point: the split is
        # established before the preprocessing that depends on it, so "fitted on: full
        # dataset" is read by somebody who already knows what the split was.
        #
        # ``applies`` says which fields this fit is asked for at all -- a regression is
        # not asked for a loss curve. Nothing is mandatory: a complete set of fifty-one
        # is not reached on a real estate, and saying so on every record helps nobody.
        "training": {
            "collection": TRAINING_RUNS_COLLECTION,
            "sections": [
                {"key": key, "title": title,
                 "fields": [f for f, spec in TRAINING_FIELD_SPECS.items()
                            if spec["section"] == key]}
                for key, title in TRAINING_SECTIONS
            ],
            # Which field each artefact is filed against, so the panel appears beside
            # the reading of the plot rather than on a documents tab away from it.
            "artefacts": TRAINING_ARTEFACTS,
            # Why each field is asked for. The first sentence reads inline; the whole
            # note sits behind the (i). A form that explains itself is one somebody
            # completes honestly rather than plausibly.
            "notes": {key: spec.get("note", "")
                      for key, spec in TRAINING_FIELD_SPECS.items()},
            "applies": [{"key": key, "when": spec["when"]}
                        for key, spec in TRAINING_FIELD_SPECS.items() if spec.get("when")],
        },
        **document_specs(),
    })


@ml_application_bp.get("")
def list_all():
    return jsonify(list_ml_applications())


@ml_application_bp.get("/<ml_application_id>")
def get_one(ml_application_id: str):
    record = get_ml_application(ml_application_id)
    if record is None:
        return jsonify({"error": "ML Application not found"}), 404
    return jsonify(record)


@ml_application_bp.post("")
def register():
    body = json_body()
    ml_application_id = body.get("ml_application_id")
    dispatch("register_ml_application", register_ml_application,
             context=context_from_request(body), ml_application_id=ml_application_id,
             fields=body.get("fields") or {})
    rebuild_ml_application_view()
    return jsonify(get_ml_application(ml_application_id)), 201


@ml_application_bp.post("/<ml_application_id>/field")
def update_field(ml_application_id: str):
    body = json_body()
    dispatch("update_ml_application_field", update_ml_application_field,
             context=context_from_request(body), ml_application_id=ml_application_id,
             field=body.get("field"), value=body.get("value"))
    rebuild_ml_application_view()
    return jsonify(get_ml_application(ml_application_id))


@ml_application_bp.post("/<ml_application_id>/retire")
def retire(ml_application_id: str):
    body = json_body()
    dispatch("retire_ml_application", retire_ml_application,
             context=context_from_request(body), ml_application_id=ml_application_id)
    rebuild_ml_application_view()
    return jsonify(get_ml_application(ml_application_id))


@ml_application_bp.post("/<ml_application_id>/collections/<collection>")
def add_item(ml_application_id: str, collection: str):
    body = json_body()
    dispatch("add_collection_item", add_collection_item,
             context=context_from_request(body), ml_application_id=ml_application_id,
             collection=collection, fields=body.get("fields") or {})
    rebuild_ml_application_view()
    return jsonify(get_ml_application(ml_application_id)), 201


@ml_application_bp.post("/<ml_application_id>/collections/<collection>/<item_id>")
def update_item(ml_application_id: str, collection: str, item_id: str):
    body = json_body()
    dispatch("update_collection_item", update_collection_item,
             context=context_from_request(body), ml_application_id=ml_application_id,
             collection=collection, item_id=item_id, fields=body.get("fields") or {})
    rebuild_ml_application_view()
    return jsonify(get_ml_application(ml_application_id))


@ml_application_bp.post("/<ml_application_id>/collections/<collection>/<item_id>/delete")
def delete_item(ml_application_id: str, collection: str, item_id: str):
    body = json_body()
    dispatch("remove_collection_item", remove_collection_item,
             context=context_from_request(body), ml_application_id=ml_application_id,
             collection=collection, item_id=item_id)
    rebuild_ml_application_view()
    return jsonify(get_ml_application(ml_application_id))


@ml_application_bp.get("/<ml_application_id>/risk-rating")
def risk_rating(ml_application_id: str):
    """Composite risk rating + heatmap -- the same engine a model and a Product use.

    Decision 8: an ML Application carries the same three dimensions and the same
    bands, so it is rated by the same code rather than by a second implementation
    that would drift from it.
    """
    record = get_ml_application(ml_application_id)
    if record is None:
        return jsonify({"error": "ML Application not found"}), 404
    return jsonify(compute_risk_rating(record["data"] or {}, as_of=date.today().isoformat()))


@ml_application_bp.get("/<ml_application_id>/mrc")
def responsible_mrc(ml_application_id: str):
    """The committee responsible for this ML Application, from its Division and Line of
    Business — resolved the same way a model's is, so the two cannot disagree about
    which committee covers the same org unit."""
    record = get_ml_application(ml_application_id)
    if record is None:
        return jsonify({"error": "ML Application not found"}), 404
    data = record["data"] or {}
    return jsonify(resolve_mrc_for_org(data.get("division"), data.get("line_of_business")))
