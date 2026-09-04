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
"""The change register: propose a change against a record, and classify it.

One endpoint set for all three record types. The subject adapter
(``src/web/_signoff_subject.py``) is what makes that possible -- the same table the
committee routing uses to find a record without knowing which kind it is.

``before`` is never taken from the request. A proposal says what it wants the record to
become; what the record IS today is read here, from the record. A client-supplied
``before`` would let a caller choose its own tier by misdescribing the starting point,
which in a register whose whole output is a severity is the only interesting way to
cheat it.
"""
from __future__ import annotations

from typing import Any

from flask import Blueprint, jsonify, request

from config.governance._change import (CHANGE_CLASSES, CHANGE_CLASS_NOTES,
                                       REVALIDATION_DEPTHS, SUBJECT_WORKFLOWS,
                                       WORKFLOW_LABELS, revalidation_depth_for)
from src.command import dispatch
from src.governance.change import (classify_change, get_change, list_changes,
                                   list_changes_for, propose_change,
                                   rebuild_change_view, supersede_change)
from src.governance.collections import next_item_id
from src.web._helpers import context_from_request, json_body
from src.web._signoff_subject import subject_by_kind

change_bp = Blueprint("change", __name__, url_prefix="/api/changes")

_ID_PREFIX = "CHG"


def _next_change_id() -> str:
    """One past the highest number in the register.

    Reuses the collection numbering rather than restating it: the reason it exists —
    numbering from a count reissues an id as soon as one is removed — applies to a
    register of proposals exactly as it does to a list of documents.
    """
    return next_item_id([{"item_id": row["change_id"]} for row in list_changes()],
                        _ID_PREFIX)


def _subject_record(subject_type: str, subject_id: str) -> tuple[Any, dict | None]:
    subject = subject_by_kind(subject_type)
    if subject is None:
        return None, None
    return subject, subject.get(subject_id)


@change_bp.get("/vocabulary")
def vocabulary():
    """The tiers, the depths and which workflow each record type belongs to.

    The console reads this once so no screen carries its own copy of the tier names —
    the same reason the risk policy is served rather than compiled into the JS.
    """
    return jsonify({
        "change_classes": list(CHANGE_CLASSES),
        "class_notes": dict(CHANGE_CLASS_NOTES),
        "revalidation_depths": dict(REVALIDATION_DEPTHS),
        "subject_workflows": dict(SUBJECT_WORKFLOWS),
        "workflow_labels": dict(WORKFLOW_LABELS),
        "depth_matrix": {change_class: {workflow: revalidation_depth_for(change_class,
                                                                        workflow)
                                        for workflow in set(SUBJECT_WORKFLOWS.values())}
                         for change_class in CHANGE_CLASSES},
    })


@change_bp.get("")
def list_register():
    """The register, optionally narrowed to one record."""
    subject_type = request.args.get("subject_type")
    subject_id = request.args.get("subject_id")
    open_only = request.args.get("open") == "1"
    if subject_type and subject_id:
        rows = list_changes_for(subject_type, subject_id,
                                include_superseded=not open_only)
    else:
        rows = list_changes(include_superseded=not open_only)
    return jsonify(rows)


@change_bp.get("/<change_id>")
def detail(change_id: str):
    record = get_change(change_id)
    if record is None:
        return jsonify({"error": "Change not found"}), 404
    return jsonify(record)


@change_bp.post("")
def propose():
    """Propose a change. 404s on a record that does not exist, before anything is written.

    The order matters: an aggregate created against a mistyped id could not be deleted
    afterwards, only superseded, leaving a proposal in the register that points at
    nothing.
    """
    body = json_body()
    subject_type = body.get("subject_type") or ""
    subject_id = body.get("subject_id") or ""
    subject, record = _subject_record(subject_type, subject_id)
    if subject is None:
        return jsonify({"error": f"unknown record type: {subject_type}"}), 404
    if record is None:
        return jsonify({"error": f"{subject_type} {subject_id} not found"}), 404
    after = body.get("after") or {}
    current = record.get("data") or {}
    change_id = _next_change_id()
    dispatch("propose_change", propose_change, context=context_from_request(body),
             change_id=change_id, subject_type=subject_type, subject_id=subject_id,
             rationale=body.get("rationale") or "",
             before={key: current.get(key) for key in after},
             after=after, affected_artifacts=body.get("affected_artifacts") or [])
    rebuild_change_view()
    return jsonify(get_change(change_id)), 201


@change_bp.post("/<change_id>/classify")
def classify(change_id: str):
    """Run the engine over a proposal and record the tier and depth it resolves to."""
    body = json_body()
    dispatch("classify_change", classify_change, context=context_from_request(body),
             change_id=change_id)
    rebuild_change_view()
    return jsonify(get_change(change_id))


@change_bp.post("/<change_id>/supersede")
def supersede(change_id: str):
    """Close a proposal that a later one replaces, or that will not be pursued."""
    body = json_body()
    dispatch("supersede_change", supersede_change, context=context_from_request(body),
             change_id=change_id)
    rebuild_change_view()
    return jsonify(get_change(change_id))
