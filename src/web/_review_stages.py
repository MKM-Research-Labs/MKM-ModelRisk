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
"""The review workflow's stages and interim approvals, for any governed record.

Written once and attached to each record type through the ``Subject`` adapter, because
a model, an ML Application and an AI System are the same kind of thing to model
governance and are reviewed identically. The alternative -- a second implementation per
record type -- is how two review workflows come to disagree about what "signed off"
means, and then only one of them is trusted.

Exactly two things vary between record types, both resolved from config through the
Subject: which collection holds the questionnaire the "questions" stage works through,
and what that stage is called. The stages themselves, their order, their statuses and
the append-only progress register do not vary, and there is no hook here for making
them vary.
"""
from __future__ import annotations

from datetime import datetime, timezone

from flask import jsonify

from config.governance import (CYCLE_START_STAGE, DEFAULT_REVIEW_STATUS,
                               VALID_REVIEW_TRIGGERS, VALID_REVIEWER_VERDICTS)
from config.governance._review import (NEW_VERSION_CHECKLIST,
                                       NEW_VERSION_TRIGGER,
                                       REVIEW_BRIEF_FIELDS,
                                       REVIEW_PROGRESS_COLLECTION)
from src.command import require_confirmation
from src.web._helpers import context_from_request, json_body

REVIEW_PROGRESS = REVIEW_PROGRESS_COLLECTION


def stamped_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def current_cycle(rows: list) -> list:
    """The progress rows belonging to the review now in flight."""
    last_marker = -1
    for index, row in enumerate(rows):
        if row.get("stage") == CYCLE_START_STAGE:
            last_marker = index
    return [r for r in rows[last_marker + 1:] if r.get("stage") != CYCLE_START_STAGE]


def approvals(record: dict) -> dict:
    """The latest interim approval per stage, keyed by stage.

    Scoped to the *current* cycle. The register is append-only -- a stage reopened and
    re-agreed leaves both rows standing, and starting a new review writes a marker
    rather than clearing anything -- so this reads forward from the last marker and
    takes the last word on each stage after it. A record re-reviewed every year
    therefore shows this year's progress, with last year's still on the record behind
    it.
    """
    rows = record["data"].get(REVIEW_PROGRESS) or []
    latest: dict = {}
    for row in current_cycle(rows):
        if row.get("stage"):
            latest[row["stage"]] = row
    return latest


def cycles(record: dict) -> list:
    """Every recorded start of a review, oldest first."""
    return [r for r in (record["data"].get(REVIEW_PROGRESS) or [])
            if r.get("stage") == CYCLE_START_STAGE]


def stage_by_key(subject) -> dict:
    """This record type's stages, keyed -- its wording, the shared keys."""
    return {stage["key"]: stage for stage in subject.review_stages()}


def review_specs(subject) -> dict:
    """The review's shape for the console, in this record type's own wording.

    Served rather than restated in JavaScript, for the reason the field specs are: the
    stage list, the verdicts and the triggers are config, and a console carrying its own
    copy is a console that offers an adopter's renamed stage under the old name -- or,
    worse, offers a trigger the start-cycle endpoint then refuses.
    """
    return {
        "review_stages": [
            {"key": stage["key"], "label": stage["label"], "status": stage["status"]}
            for stage in subject.review_stages()
        ],
        "review_questions_collection": subject.questions_collection(),
        "reviewer_verdicts": list(VALID_REVIEWER_VERDICTS),
        "review_triggers": list(VALID_REVIEW_TRIGGERS),
        "new_version_trigger": NEW_VERSION_TRIGGER,
        "review_brief_fields": list(REVIEW_BRIEF_FIELDS),
        "new_version_checklist": list(NEW_VERSION_CHECKLIST),
    }


def register_review_stage_routes(blueprint, subject) -> None:
    """Attach approve-stage, question-verdict and start-cycle for one record type.

    The URL parameter is named ``subject_id`` throughout. That changes no URL -- a
    Flask route's parameter name is not part of the path -- and it is what lets one
    set of handlers serve ``/api/models/...``, ``/api/ml-applications/...`` and
    ``/api/ai-systems/...`` without three copies differing only in a noun.
    """
    # The Subject carries how its record type reads in a sentence written for a
    # person. Derived from ``kind`` here until main brought a better answer:
    # "the ai_system was not found" is what string-munging a machine key gets you.
    noun = subject.noun

    def _load(subject_id):
        record = subject.get(subject_id)
        return record, (None if record else (jsonify({"error": f"{noun} not found"}), 404))

    @blueprint.post("/<subject_id>/review/approve-stage")
    def approve_stage(subject_id: str):
        """Record the reviewer's interim approval of one review stage.

        This is not a lock: earlier stages stay open afterwards, because a reviewer who
        reaches the limitations and needs to reopen a question must be able to. What it
        records is that the stage was agreed, by whom, and when -- and it carries the
        record's review status forward to match.
        """
        record, missing = _load(subject_id)
        if missing:
            return missing
        body = json_body()
        stage = stage_by_key(subject).get(body.get("stage"))
        if stage is None:
            return jsonify({"error": f"unknown review stage: {body.get('stage')}"}), 400
        ctx = context_from_request(body)
        # Agreeing a stage moves a governance record on and names the person who
        # agreed it, so it is confirmed like every other amendment.
        require_confirmation("approve_review_stage", ctx)
        subject.add_item_as("approve_review_stage", ctx, subject_id, REVIEW_PROGRESS, {
            "stage": stage["key"], "stage_label": stage["label"],
            "status": stage["status"], "note": (body.get("note") or "").strip(),
            "approved_by": ctx.principal.actor, "approved_at": stamped_now(),
        })
        subject.set_field_as("approve_review_stage", ctx, subject_id,
                             "review_status", stage["status"])
        subject.rebuild()
        return jsonify(subject.get(subject_id)), 201

    @blueprint.post("/<subject_id>/review/question-verdict")
    def question_verdict(subject_id: str):
        """Record the reviewer's verdict on one of the review questions.

        The owner's status and the reviewer's verdict are separate answers to the same
        question and may disagree -- a question can be Addressed by its owner and
        Challenged by its reviewer, which is the review doing its job. Who reviewed it
        and when are stamped here rather than sent by the console: an attribution the
        browser supplies is not evidence of anything.
        """
        record, missing = _load(subject_id)
        if missing:
            return missing
        collection = subject.questions_collection()
        if collection is None:
            return jsonify({"error": f"a {noun} has no review questionnaire"}), 400
        body = json_body()
        verdict = body.get("verdict")
        if verdict not in VALID_REVIEWER_VERDICTS:
            allowed = ", ".join(VALID_REVIEWER_VERDICTS)
            return jsonify({"error": f"reviewer verdict must be one of: {allowed}"}), 400
        ctx = context_from_request(body)
        subject.update_item_as(
            "record_reviewer_verdict", ctx, subject_id, collection, body.get("item_id"),
            {"reviewer_verdict": verdict,
             "reviewer_comment": (body.get("comment") or "").strip(),
             "reviewed_by": ctx.principal.actor, "reviewed_at": stamped_now()})
        subject.rebuild()
        return jsonify(subject.get(subject_id))

    @blueprint.post("/<subject_id>/review/start-cycle")
    def start_cycle(subject_id: str):
        """Start a review, recording why it is happening.

        A review is not only a calendar event. It starts because the owner asks for one
        -- particularly when ownership has just changed and the new owner has to satisfy
        themselves -- because a material new version has landed, or because the
        committee directed it. What the reviewer should look at differs in each case, so
        the trigger is recorded rather than assumed.

        Nothing is erased. The stage register is append-only, so this writes a marker;
        progress is read forward from it, and the previous cycle's approvals, notes and
        filed report stay exactly where they are.
        """
        record, missing = _load(subject_id)
        if missing:
            return missing
        body = json_body()
        trigger = body.get("trigger")
        if trigger not in VALID_REVIEW_TRIGGERS:
            allowed = ", ".join(VALID_REVIEW_TRIGGERS)
            return jsonify({"error": f"a review trigger must be one of: {allowed}"}), 400
        ctx = context_from_request(body)
        # Starting a review resets what the console shows as outstanding, so it is
        # confirmed like any other amendment.
        require_confirmation("start_review_cycle", ctx)
        subject.add_item_as("start_review_cycle", ctx, subject_id, REVIEW_PROGRESS, {
            "stage": CYCLE_START_STAGE, "stage_label": "Review started",
            "status": DEFAULT_REVIEW_STATUS, "note": (body.get("note") or "").strip(),
            "approved_by": ctx.principal.actor, "approved_at": stamped_now()})
        for field, value in (("review_trigger", trigger),
                             ("review_status", DEFAULT_REVIEW_STATUS)):
            subject.set_field_as("start_review_cycle", ctx, subject_id, field, value)
        subject.rebuild()
        return jsonify(subject.get(subject_id)), 201

    # Endpoint names are namespaced by blueprint, so the same three names on three
    # blueprints do not collide. Returned for nothing but readability at the call site.
    return (approve_stage, question_verdict, start_cycle)
