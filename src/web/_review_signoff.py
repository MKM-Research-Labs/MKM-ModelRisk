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

Kept apart from the stages it closes, because this is where the workflow stops being
editable and becomes a document a committee relies on. Shared across record types for
the reason the rest of the review is: a model, an ML Application and an AI System are
model-governed records, and "signed off" has to mean the same thing for all three or it
means nothing for any of them.
"""
from __future__ import annotations

from datetime import date

from flask import jsonify

from config.governance import REVIEW_REPORT_CATEGORY, SIGNED_OFF_REVIEW_STATUS
from src.command import require_confirmation
from src.governance.documents import add_document
from src.governance.model_inventory.review_report import render_review_report_pdf
from src.governance.mrc_settings import get_settings
from src.web._helpers import context_from_request, json_body
from src.web._review_stages import approvals, stamped_now
from src.web._review_thread import open_challenges

REVIEW_SIGNOFFS = "review_signoffs"


def signoff_blockers(data: dict, approvals_by_stage: dict, stages: tuple) -> list[str]:
    """What stands between this review and a sign-off, in the reviewer's words.

    Named here so the console and the endpoint cannot disagree about it: the button says
    why it is disabled, and the endpoint refuses for exactly the same reasons. An open
    challenge blocks -- a reviewer who means to sign off over one has to answer it
    first, in writing, rather than signing past it in silence.
    """
    blockers = [stage["label"] + " not agreed"
                for stage in stages if stage["key"] not in approvals_by_stage]
    open_ones = open_challenges(data)
    if open_ones:
        blockers.append(
            str(len(open_ones)) + " open challenge" + ("" if len(open_ones) == 1 else "s")
            + " (" + ", ".join(c["item_id"] for c in open_ones) + ")")
    return blockers


def register_review_signoff_routes(blueprint, subject) -> None:
    """Attach the blockers and sign-off endpoints for one record type."""
    noun = subject.kind.replace("_", " ")

    def _blockers(record):
        return signoff_blockers(record.get("data") or {}, approvals(record),
                                subject.review_stages())

    @blueprint.get("/<subject_id>/review/blockers")
    def review_blockers(subject_id: str):
        """What is standing in the way of sign-off, for the console to show."""
        record = subject.get(subject_id)
        if record is None:
            return jsonify({"error": f"{noun} not found"}), 404
        return jsonify({"blockers": _blockers(record)})

    @blueprint.post("/<subject_id>/review/sign-off")
    def sign_off(subject_id: str):
        """Close the review: record the reviewer's commentary and file the report.

        The report is generated here, at the moment of signing, and filed against the
        record -- the same shape as closing a meeting generating and filing its minutes.
        It is what the MRC receives when it signs off the risk rating; the committee
        does not adjudicate the review itself.
        """
        record = subject.get(subject_id)
        if record is None:
            return jsonify({"error": f"{noun} not found"}), 404
        data = record.get("data") or {}
        body = json_body()
        commentary = (body.get("commentary") or "").strip()
        if not commentary:
            return jsonify({"error": "a sign-off needs the reviewer's final commentary"}), 400
        blockers = _blockers(record)
        if blockers:
            return jsonify({"error": "the review is not finished: " + "; ".join(blockers)}), 400
        ctx = context_from_request(body)
        # Signing off is a governance act naming the person who made it; confirm before
        # any work is done, so an unconfirmed call never generates a document.
        require_confirmation("sign_off_review", ctx)

        as_of = date.today().isoformat()
        signoff = {"commentary": commentary, "signed_by": ctx.principal.actor,
                   "signed_at": stamped_now()}
        pdf = render_review_report_pdf(
            record, get_settings(), signoff, as_of, approvals(record),
            id_key=subject.id_key, questions_collection=subject.questions_collection(),
            stages=subject.review_stages())
        filename = f"{subject_id}_model_review_report_{as_of}.pdf"
        meta = add_document(
            aggregate_type=subject.aggregate_type, aggregate_id=subject_id,
            scope=subject.doc_scope(subject_id), category=REVIEW_REPORT_CATEGORY,
            filename=filename, data=pdf,
            description=f"Model Review Report signed off {as_of}",
            actor=ctx.principal.actor)
        subject.add_item_as("sign_off_review", ctx, subject_id, REVIEW_SIGNOFFS,
                            {**signoff, "report_filename": meta["filename"],
                             "report_original_name": meta.get("original_name") or filename})
        subject.set_field_as("sign_off_review", ctx, subject_id,
                             "review_status", SIGNED_OFF_REVIEW_STATUS)
        subject.rebuild()
        return jsonify(subject.get(subject_id)), 201

    return review_blockers, sign_off
