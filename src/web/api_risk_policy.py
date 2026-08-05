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
"""Read the risk policy for the console.

Returns the firm-wide seed plus each division's live (MRC-approved) policy, so the UI
can resolve risk-rating colours, labels, ordering and the tier/Mission-Criticality
vocabulary per a model's division. The console loads this once at startup.
"""
from __future__ import annotations

from datetime import date

from flask import Blueprint, Response, jsonify, request, send_file

from src.command import dispatch
from src.files import UploadError, save_upload, upload_path
from src.governance.mrc_settings import get_settings
from src.governance.risk_policy import (
    approve_policy,
    default_policy,
    get_risk_policy,
    load,
    propose_policy,
    reject_policy,
    set_policy_document,
)
from src.governance.risk_policy.document import render_policy_document_pdf
from src.web._helpers import context_from_request, json_body, reference_options, request_actor

risk_policy_bp = Blueprint("risk_policy", __name__)
_DOCUMENT_SCOPE = "risk_policy"


@risk_policy_bp.get("/api/risk-policy")
def risk_policy_registry():
    """The seed policy + every division's live policy, keyed by division name."""
    divisions = reference_options().get("division") or []
    return jsonify({
        "seed": default_policy(),
        "divisions": {division: get_risk_policy(division) for division in divisions},
    })


def _detail(division: str) -> dict:
    state = load(division)
    return {"division": division, "live": state["live"], "draft": state["draft"],
            "document": state["document"], "state": state["state"], "seed": default_policy()}


@risk_policy_bp.get("/api/risk-policy/<division>")
def risk_policy_detail(division: str):
    """One division's policy for the Admin editor: its live (approved) policy, any draft
    awaiting MRC sign-off, the uploaded policy document, and the lifecycle state."""
    return jsonify(_detail(division))


@risk_policy_bp.post("/api/risk-policy/<division>/propose")
def propose_risk_policy(division: str):
    """Save a division's edited policy as a draft for its MRC to sign off. The draft does
    not affect any model until approved at the division's MRC meeting."""
    body = json_body()
    dispatch("propose_risk_policy", propose_policy, context=context_from_request(body),
             division=division, policy=body.get("policy"))
    return jsonify(_detail(division))


@risk_policy_bp.post("/api/risk-policy/<division>/approve")
def approve_risk_policy(division: str):
    """Ratify the division's pending draft — its MRC has signed it off, so it becomes the
    live policy. Called from the division's MRC meeting, which it records for the audit."""
    body = json_body()
    dispatch("approve_risk_policy", approve_policy, context=context_from_request(body),
             division=division, meeting_id=body.get("meeting_id"))
    return jsonify(_detail(division))


@risk_policy_bp.post("/api/risk-policy/<division>/reject")
def reject_risk_policy(division: str):
    """Decline the division's pending draft at its MRC. The live policy is unchanged."""
    body = json_body()
    dispatch("reject_risk_policy", reject_policy, context=context_from_request(body),
             division=division, meeting_id=body.get("meeting_id"))
    return jsonify(_detail(division))


@risk_policy_bp.get("/api/risk-policy/<division>/categorisation.pdf")
def risk_categorisation_pdf(division: str):
    """The division's proposed (or live) risk categorisation as a PDF for the MRC to sign
    off — distinct from the uploaded Risk Policy document."""
    pdf = render_policy_document_pdf(division, get_settings(), date.today().isoformat())
    return Response(pdf, mimetype="application/pdf", headers={
        "Content-Disposition": 'inline; filename="' + division + ' Risk Categorisation.pdf"'})


@risk_policy_bp.post("/api/risk-policy/<division>/document")
def upload_risk_policy_document(division: str):
    """Upload the division's formal written risk-policy document (PDF/Word)."""
    file = request.files.get("file")
    if file is None:
        return jsonify({"error": "no file provided"}), 400
    try:
        meta = save_upload(_DOCUMENT_SCOPE, file.filename, file.read())
    except UploadError as exc:
        return jsonify({"error": str(exc)}), 400
    set_policy_document(division=division, filename=meta["filename"],
                        original_name=meta["original_name"], actor=request_actor())
    return jsonify(_detail(division)), 201


@risk_policy_bp.get("/api/risk-policy/<division>/document")
def download_risk_policy_document(division: str):
    """Download the division's uploaded risk-policy document, if any."""
    document = load(division)["document"]
    if not document:
        return jsonify({"error": "no policy document uploaded"}), 404
    path = upload_path(_DOCUMENT_SCOPE, document["filename"])
    if not path.exists():
        return jsonify({"error": "policy document file missing"}), 404
    return send_file(str(path), as_attachment=True, download_name=document["original_name"])
