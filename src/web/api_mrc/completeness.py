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
"""Per-MRC completeness audit: run the governance completeness audit scoped to
one committee's in-scope models and products, save it as a per-meeting PDF, and
serve the latest version.

The audit is the same scan/scoring engine used by the global Audit Reports tab
(``src.governance.completeness``); here it is filtered to what the committee
actually oversees and pinned to the standing "Governance completeness audit"
agenda item so the committee can run it, re-run it until the meeting closes, and
sign it off. Attached to the shared ``mrc_bp``."""
from __future__ import annotations

from datetime import date, datetime

from flask import jsonify, send_file

from src.files import store_generated, upload_path
from src.governance.completeness.report import render_completeness_pdf
from src.governance.completeness.scan import scan
from src.governance.mrc import (
    get_meeting as get_meeting_raw,
    get_meeting_enriched as get_meeting,
    rebuild_meeting_view,
    update_collection_item,
)
from src.governance.mrc.pack import TectonicNotFound
from src.governance.mrc_settings import get_settings
from src.governance.reference import get_reference_lists
from src.web._helpers import request_actor
from src.web.api_mrc._bp import mrc_bp

AUDIT_SCOPE = "meeting_audit"
AUDIT_KIND = "completeness_audit"


def _actor_name(actor: str) -> str:
    """Resolve an actor identity (an email) to the person's name from the People
    directory, so the audit records who ran it by name rather than by login.
    Falls back to the raw identity when it isn't a registered person."""
    for person in (get_reference_lists().get("people") or []):
        if person.get("email") == actor:
            return person.get("name") or actor
    return actor


def _audit_item(meeting: dict) -> dict | None:
    """The standing completeness-audit agenda item, if the meeting has one.

    Meetings scheduled before this feature existed have no such item until the
    backfill (scripts/backfill_completeness_audit_item.py) adds it."""
    for item in (meeting["data"].get("agenda") or []):
        if item.get("kind") == AUDIT_KIND:
            return item
    return None


def _scope_ids(data: dict) -> tuple[list[str], list[str]]:
    """The model and product ids in scope for this committee's meeting."""
    model_ids = [i["model_id"] for i in (data.get("models_in_scope") or [])
                 if i.get("model_id")]
    product_ids = [i["product_id"] for i in (data.get("products_in_scope") or [])
                   if i.get("product_id")]
    return model_ids, product_ids


@mrc_bp.post("/<meeting_id>/completeness-audit/run")
def run_completeness_audit(meeting_id: str):
    """Run (or re-run) the completeness audit scoped to this committee, save the
    PDF and stamp the standing agenda item with the latest version's metadata.

    Re-running overwrites the saved PDF and bumps the version; the event log keeps
    the full history of runs. A closed meeting is immutable, so runs stop at close.
    """
    meeting = get_meeting_raw(meeting_id)
    if meeting is None:
        return jsonify({"error": "meeting not found"}), 404
    d = meeting["data"] or {}
    if d.get("status") == "Completed":
        return jsonify({"error": "meeting is closed"}), 400
    item = _audit_item(meeting)
    if item is None:
        return jsonify({"error": "no completeness-audit item on this meeting"}), 404

    model_ids, product_ids = _scope_ids(d)
    as_of = date.today().isoformat()
    rows = scan(as_of, model_ids=model_ids, product_ids=product_ids)
    try:
        pdf = render_completeness_pdf(get_settings(), as_of, rows=rows)
    except TectonicNotFound as exc:
        # Optional system dependency missing: surface an actionable 503 rather
        # than a 500, mirroring the global Audit Reports endpoint.
        return jsonify({"error": str(exc)}), 503
    meta = store_generated(AUDIT_SCOPE, f"audit_{meeting_id}.pdf", pdf)

    version = int(item.get("audit_version") or 0) + 1
    findings = sum(len(r.get("gaps") or []) for r in rows)
    update_collection_item(
        meeting_id=meeting_id, collection="agenda", item_id=item["item_id"],
        fields={
            "audit_version": str(version),
            "audit_filename": meta["filename"],
            "audit_original_name": meta["original_name"],
            "audit_generated_at": datetime.now().isoformat(timespec="minutes"),
            "audit_generated_by": _actor_name(request_actor()),
            "audit_entities": str(len(rows)),
            "audit_findings": str(findings),
        },
        actor=request_actor(),
    )
    rebuild_meeting_view()
    return jsonify(get_meeting(meeting_id)), 200


@mrc_bp.get("/<meeting_id>/completeness-audit.pdf")
def completeness_audit_pdf(meeting_id: str):
    """Serve the latest saved completeness-audit PDF for the meeting."""
    meeting = get_meeting(meeting_id)
    if meeting is None:
        return jsonify({"error": "meeting not found"}), 404
    item = _audit_item(meeting)
    filename = (item or {}).get("audit_filename")
    if not filename:
        return jsonify({"error": "audit not generated yet"}), 404
    path = upload_path(AUDIT_SCOPE, filename)
    if not path.exists():
        return jsonify({"error": "audit file missing"}), 404
    return send_file(str(path), mimetype="application/pdf",
                     download_name=f"mrc_{meeting_id}_completeness_audit.pdf")
