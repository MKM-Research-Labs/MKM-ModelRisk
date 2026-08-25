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
"""MRC sign-off for an ML Application.

The ML twin of ``api_models_signoff``. An ML Application's rating goes to the
committee exactly as a model's does: the owner PROPOSES a rating, it is routed to the
committee responsible for the record's division, and the stored rating does not move
until that committee approves it.

Before this existed an ML rating applied directly — which meant the one class of
record most likely to be argued about was the one class exempt from the committee
that signs off everything else.
"""
from __future__ import annotations

from flask import jsonify

from src.governance.ml_application import get_ml_application
from src.governance.ml_application.review_scope import guard_review_complete
from src.governance.mrc import matching_mrc
from src.governance.reference import get_reference_lists
from src.web._helpers import context_from_request, json_body
from src.web._ml_scope import scoped
from src.web._signoff_routing import raise_signoff
from src.web._signoff_subject import ML_APPLICATION_SUBJECT
from src.web.api_ml_application import ml_application_bp


def _target_mrc(record: dict):
    """The committee responsible for this ML Application, or an error response."""
    data = record["data"] or {}
    mrc, _level = matching_mrc(data.get("division"), data.get("line_of_business"),
                               get_reference_lists())
    if mrc is None:
        return None, (jsonify({"error": "no MRC committee covers this ML Application's "
                                        "division / line of business — configure one "
                                        "under Admin → MRC first"}), 400)
    return mrc, None


@ml_application_bp.post("/<ml_application_id>/request-signoff")
def request_signoff(ml_application_id: str):
    """Propose a rating to the committee. Attached to a Scheduled meeting at once,
    otherwise left Pending for the next meeting of that committee to pick up."""
    record = get_ml_application(ml_application_id)
    if record is None:
        return jsonify({"error": "ML Application not found"}), 404
    body = json_body()
    proposed_rag = body.get("proposed_rag")
    if not proposed_rag:
        return jsonify({"error": "proposed_rag is required"}), 400
    mrc, error = _target_mrc(record)
    if error:
        return error
    # The committee is asked to sign off a review, so the review has to be one. Raised
    # as a DomainError, which the app turns into a 400 naming what is still blank --
    # the same wall a script hits, because the check is not in this route's logic.
    guard_review_complete(record["data"] or {}, "Raising this for MRC sign-off")
    raise_signoff(context_from_request(body), ML_APPLICATION_SUBJECT, ml_application_id,
                  kind="rag", proposed_rag=proposed_rag, target_mrc=mrc["value"],
                  note=body.get("note"))
    return jsonify(scoped(get_ml_application(ml_application_id))), 201
