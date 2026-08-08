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
"""The review workflow's stages and their interim approvals.

The reviewer approves a stage; the review moves on and the model's review status
follows. Both happen here rather than in the console, so the mapping from stage to
status is one rule in one place and a stage cannot be approved without the status
that goes with it. The thread and the sign-off have modules of their own.
Registered on the shared ``models_bp`` blueprint.
"""
from __future__ import annotations

from datetime import datetime, timezone

from flask import jsonify

from config.governance import (CYCLE_START_STAGE, DEFAULT_REVIEW_STATUS,
                               REVIEW_STAGES, VALID_REVIEW_TRIGGERS,
                               VALID_REVIEWER_VERDICTS)
from src.command import dispatch, require_confirmation
from src.governance.model_inventory import get_model
from src.governance.model_inventory.commands import (add_collection_item,
                                                     update_collection_item,
                                                     update_model_field)
from src.governance.model_inventory.projection import rebuild_inventory_view
from src.web._helpers import context_from_request, json_body
from src.web.api_models import models_bp

REVIEW_PROGRESS = "review_progress"
VALIDATION_QUESTIONS = "validation_questions"
_STAGE_BY_KEY = {stage["key"]: stage for stage in REVIEW_STAGES}


def _stamped_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def approvals(model: dict) -> dict:
    """The latest interim approval per stage, keyed by stage.

    Scoped to the *current* cycle. The register is append-only — a stage reopened
    and re-agreed leaves both rows standing, and starting a new review writes a
    marker rather than clearing anything — so this reads forward from the last
    marker and takes the last word on each stage after it. A model re-reviewed
    every year therefore shows this year's progress, with last year's still on the
    record behind it.
    """
    rows = model["data"].get(REVIEW_PROGRESS) or []
    latest: dict = {}
    for row in _current_cycle(rows):
        if row.get("stage"):
            latest[row["stage"]] = row
    return latest


def _current_cycle(rows: list) -> list:
    """The progress rows belonging to the review now in flight."""
    last_marker = -1
    for index, row in enumerate(rows):
        if row.get("stage") == CYCLE_START_STAGE:
            last_marker = index
    return [r for r in rows[last_marker + 1:] if r.get("stage") != CYCLE_START_STAGE]


def cycles(model: dict) -> list:
    """Every recorded start of a review, oldest first."""
    return [r for r in (model["data"].get(REVIEW_PROGRESS) or [])
            if r.get("stage") == CYCLE_START_STAGE]


@models_bp.post("/<model_id>/review/approve-stage")
def approve_stage(model_id: str):
    """Record the reviewer's interim approval of one review stage.

    This is not a lock: earlier stages stay open afterwards, because a reviewer who
    reaches the limitations and needs to reopen a question must be able to. What it
    records is that the stage was agreed, by whom, and when — and it carries the
    model's review status forward to match.
    """
    model = get_model(model_id)
    if model is None:
        return jsonify({"error": "model not found"}), 404
    body = json_body()
    stage = _STAGE_BY_KEY.get(body.get("stage"))
    if stage is None:
        return jsonify({"error": f"unknown review stage: {body.get('stage')}"}), 400
    ctx = context_from_request(body)
    # Agreeing a stage moves a governance record on and names the person who
    # agreed it, so it is confirmed like every other amendment.
    require_confirmation("approve_review_stage", ctx)
    fields = {
        "stage": stage["key"], "stage_label": stage["label"], "status": stage["status"],
        "note": (body.get("note") or "").strip(),
        "approved_by": ctx.principal.actor,
        "approved_at": _stamped_now(),
    }
    dispatch(
        "approve_review_stage", add_collection_item, context=ctx,
        model_id=model_id, collection=REVIEW_PROGRESS, fields=fields,
    )
    dispatch(
        "approve_review_stage", update_model_field, context=ctx,
        model_id=model_id, field="review_status", value=stage["status"],
    )
    rebuild_inventory_view()
    return jsonify(get_model(model_id)), 201


@models_bp.post("/<model_id>/review/question-verdict")
def question_verdict(model_id: str):
    """Record the reviewer's verdict on one of the nine questions.

    The owner's status and the reviewer's verdict are separate answers to the same
    question and may disagree — a question can be Addressed by its owner and
    Challenged by its reviewer, which is the review doing its job. Who reviewed it
    and when are stamped here rather than sent by the console: an attribution the
    browser supplies is not evidence of anything.
    """
    model = get_model(model_id)
    if model is None:
        return jsonify({"error": "model not found"}), 404
    body = json_body()
    item_id = body.get("item_id")
    verdict = body.get("verdict")
    if verdict not in VALID_REVIEWER_VERDICTS:
        allowed = ", ".join(VALID_REVIEWER_VERDICTS)
        return jsonify({"error": f"reviewer verdict must be one of: {allowed}"}), 400
    ctx = context_from_request(body)
    fields = {
        "reviewer_verdict": verdict,
        "reviewer_comment": (body.get("comment") or "").strip(),
        "reviewed_by": ctx.principal.actor,
        "reviewed_at": _stamped_now(),
    }
    dispatch(
        "record_reviewer_verdict", update_collection_item, context=ctx,
        model_id=model_id, collection=VALIDATION_QUESTIONS, item_id=item_id, fields=fields,
    )
    rebuild_inventory_view()
    return jsonify(get_model(model_id))




@models_bp.post("/<model_id>/review/start-cycle")
def start_cycle(model_id: str):
    """Start a review, recording why it is happening.

    A review is not only a calendar event. It starts because the owner asks for one
    — particularly when ownership has just changed and the new owner has to satisfy
    themselves — because a material new version has landed, or because the committee
    directed it. What the reviewer should look at differs in each case, so the
    trigger is recorded rather than assumed.

    Nothing is erased. The stage register is append-only, so this writes a marker;
    progress is read forward from it, and the previous cycle's approvals, notes and
    filed report stay exactly where they are.
    """
    model = get_model(model_id)
    if model is None:
        return jsonify({"error": "model not found"}), 404
    body = json_body()
    trigger = body.get("trigger")
    if trigger not in VALID_REVIEW_TRIGGERS:
        allowed = ", ".join(VALID_REVIEW_TRIGGERS)
        return jsonify({"error": f"a review trigger must be one of: {allowed}"}), 400
    ctx = context_from_request(body)
    # Starting a review resets what the console shows as outstanding, so it is
    # confirmed like any other amendment.
    require_confirmation("start_review_cycle", ctx)
    dispatch(
        "start_review_cycle", add_collection_item, context=ctx,
        model_id=model_id, collection=REVIEW_PROGRESS,
        fields={"stage": CYCLE_START_STAGE, "stage_label": "Review started",
                "status": DEFAULT_REVIEW_STATUS,
                "note": (body.get("note") or "").strip(),
                "approved_by": ctx.principal.actor, "approved_at": _stamped_now()},
    )
    for field, value in (("review_trigger", trigger),
                         ("review_status", DEFAULT_REVIEW_STATUS)):
        dispatch("start_review_cycle", update_model_field, context=ctx,
                 model_id=model_id, field=field, value=value)
    rebuild_inventory_view()
    return jsonify(get_model(model_id)), 201
