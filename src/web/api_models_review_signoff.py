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
"""Signing off a review: the gate, the attestation and the report it files.

Kept apart from the stages it closes, because this is where the workflow stops
being editable and becomes a document a committee relies on. Registered on the
shared ``models_bp`` blueprint.
"""
from __future__ import annotations

from datetime import date

from flask import jsonify

from config.governance import (REVIEW_DOC_CATEGORIES, REVIEW_STAGES,
                               SIGNED_OFF_REVIEW_STATUS)
from src.command import dispatch, require_confirmation
from src.governance.documents import add_document, model_scope
from src.governance.model_inventory import get_model
from src.governance.model_inventory.commands import (AGGREGATE_TYPE as MODEL_AGGREGATE,
                                                     add_collection_item,
                                                     update_model_field)
from src.governance.model_inventory.projection import rebuild_inventory_view
from src.governance.model_inventory.review_report import render_review_report_pdf
from src.governance.mrc_settings import get_settings
from src.web._helpers import context_from_request, json_body
from src.web.api_models import models_bp
from src.web.api_models_review import approvals, _stamped_now
from src.web.api_models_review_notes import open_challenges

REVIEW_SIGNOFFS = "review_signoffs"
# The review's own working papers, and where its signed report is filed.
REVIEW_DOC_CATEGORY = REVIEW_DOC_CATEGORIES[0]


def signoff_blockers(data: dict, approvals_by_stage: dict) -> list[str]:
    """What stands between this review and a sign-off, in the reviewer's words.

    Named here so the console and the endpoint cannot disagree about it: the button
    says why it is disabled, and the endpoint refuses for exactly the same reasons.
    An open challenge blocks — a reviewer who means to sign off over one has to
    answer it first, in writing, rather than signing past it in silence.
    """
    blockers = []
    for stage in REVIEW_STAGES:
        if stage["key"] not in approvals_by_stage:
            blockers.append(stage["label"] + " not agreed")
    open_ones = open_challenges(data)
    if open_ones:
        blockers.append(
            str(len(open_ones)) + " open challenge" + ("" if len(open_ones) == 1 else "s")
            + " (" + ", ".join(c["item_id"] for c in open_ones) + ")")
    return blockers


@models_bp.get("/<model_id>/review/blockers")
def review_blockers(model_id: str):
    """What is standing in the way of sign-off, for the console to show."""
    model = get_model(model_id)
    if model is None:
        return jsonify({"error": "model not found"}), 404
    return jsonify({"blockers": signoff_blockers(model.get("data") or {}, approvals(model))})


@models_bp.post("/<model_id>/review/sign-off")
def sign_off(model_id: str):
    """Close the review: record the reviewer's commentary and file the report.

    The report is generated here, at the moment of signing, and filed against the
    model — the same shape as closing a meeting generating and filing its minutes.
    It is what the MRC receives when it signs off the risk rating; the committee
    does not adjudicate the review itself.
    """
    model = get_model(model_id)
    if model is None:
        return jsonify({"error": "model not found"}), 404
    data = model.get("data") or {}
    body = json_body()
    commentary = (body.get("commentary") or "").strip()
    if not commentary:
        return jsonify({"error": "a sign-off needs the reviewer's final commentary"}), 400
    blockers = signoff_blockers(data, approvals(model))
    if blockers:
        return jsonify({"error": "the review is not finished: " + "; ".join(blockers)}), 400
    ctx = context_from_request(body)
    # Signing off is a governance act naming the person who made it; confirm before
    # any work is done, so an unconfirmed call never generates a document.
    require_confirmation("sign_off_review", ctx)

    as_of = date.today().isoformat()
    signoff = {"commentary": commentary, "signed_by": ctx.principal.actor,
               "signed_at": _stamped_now()}
    settings = get_settings()
    pdf = render_review_report_pdf(model, settings, signoff, as_of, approvals(model))
    filename = f"{model_id}_model_review_report_{as_of}.pdf"
    meta = add_document(
        aggregate_type=MODEL_AGGREGATE, aggregate_id=model_id, scope=model_scope(model_id),
        category=REVIEW_DOC_CATEGORY, filename=filename, data=pdf,
        description=f"Model Review Report signed off {as_of}", actor=ctx.principal.actor,
    )
    dispatch(
        "sign_off_review", add_collection_item, context=ctx,
        model_id=model_id, collection=REVIEW_SIGNOFFS,
        fields={**signoff, "report_filename": meta["filename"],
                "report_original_name": meta.get("original_name") or filename},
    )
    dispatch(
        "sign_off_review", update_model_field, context=ctx,
        model_id=model_id, field="review_status", value=SIGNED_OFF_REVIEW_STATUS,
    )
    rebuild_inventory_view()
    return jsonify(get_model(model_id)), 201
