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
"""MRC sign-off for an AI System.

The same trip a model and an ML Application take: the owner PROPOSES a rating, it
is routed to the committee responsible for the record's division, and the stored
rating does not move until that committee approves it. Retiring travels the same
route — hibernating a record is the committee's decision, not its owner's — and so
does bringing one back.

Built at the same time as the record rather than left for later. An ML rating
applied directly until somebody noticed it was the one class of record exempt from
the committee that signs off everything else, and the argument for the exemption was
always that the record type was new and nothing depended on it yet. That argument
applies word for word to this one.
"""
from __future__ import annotations

from flask import jsonify

from src.governance.ai_system import get_ai_system
from src.web._helpers import context_from_request, json_body
from src.web._lifecycle_request import request_lifecycle_change, target_mrc
from src.web._signoff_routing import raise_signoff
from src.web._signoff_subject import AI_SYSTEM_SUBJECT
from src.web.api_ai_system import ai_system_bp

# How the record type is named back to whoever raised the request. It lives on the
# Subject so the error, the minute and the screen all say the same word.
NOUN = AI_SYSTEM_SUBJECT.noun


@ai_system_bp.post("/<ai_system_id>/request-signoff")
def request_signoff(ai_system_id: str):
    """Propose a rating to the committee. Attached to a Scheduled meeting at once,
    otherwise left Pending for the next meeting of that committee to pick up."""
    record = get_ai_system(ai_system_id)
    if record is None:
        return jsonify({"error": f"{NOUN} not found"}), 404
    body = json_body()
    proposed_rag = body.get("proposed_rag")
    if not proposed_rag:
        return jsonify({"error": "proposed_rag is required"}), 400
    mrc, error = target_mrc(record, NOUN)
    if error:
        return error
    raise_signoff(context_from_request(body), AI_SYSTEM_SUBJECT, ai_system_id,
                  kind="rag", proposed_rag=proposed_rag, target_mrc=mrc["value"],
                  note=body.get("note"))
    return jsonify(get_ai_system(ai_system_id)), 201


@ai_system_bp.post("/<ai_system_id>/request-retire")
def request_retire(ai_system_id: str):
    """Owner asks the MRC to ratify retiring (hibernating) the AI System.

    The record stays in the estate and editable while the request is queued — it
    only drops out once the committee approves.
    """
    return request_lifecycle_change(AI_SYSTEM_SUBJECT, ai_system_id, kind="retire",
                                    expect_retired=False)


@ai_system_bp.post("/<ai_system_id>/request-reactivate")
def request_reactivate(ai_system_id: str):
    """Owner asks the MRC to ratify bringing a hibernated AI System back."""
    return request_lifecycle_change(AI_SYSTEM_SUBJECT, ai_system_id, kind="reactivate",
                                    expect_retired=True)
