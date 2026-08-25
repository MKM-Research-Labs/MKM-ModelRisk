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
rating does not move until that committee approves it.

Built at the same time as the record rather than left for later. An ML rating
applied directly until somebody noticed it was the one class of record exempt from
the committee that signs off everything else, and the argument for the exemption was
always that the record type was new and nothing depended on it yet. That argument
applies word for word to this one.
"""
from __future__ import annotations

from flask import jsonify

from src.governance.ai_system import get_ai_system
from src.governance.mrc import matching_mrc
from src.governance.reference import get_reference_lists
from src.web._helpers import context_from_request, json_body
from src.web._signoff_routing import raise_signoff
from src.web._signoff_subject import AI_SYSTEM_SUBJECT
from src.web.api_ai_system import ai_system_bp


def _target_mrc(record: dict):
    """The committee responsible for this AI System, or an error response."""
    data = record["data"] or {}
    mrc, _level = matching_mrc(data.get("division"), data.get("line_of_business"),
                               get_reference_lists())
    if mrc is None:
        return None, (jsonify({"error": "no MRC committee covers this AI System's "
                                        "division / line of business — configure one "
                                        "under Admin → MRC first"}), 400)
    return mrc, None


@ai_system_bp.post("/<ai_system_id>/request-signoff")
def request_signoff(ai_system_id: str):
    """Propose a rating to the committee. Attached to a Scheduled meeting at once,
    otherwise left Pending for the next meeting of that committee to pick up."""
    record = get_ai_system(ai_system_id)
    if record is None:
        return jsonify({"error": "AI System not found"}), 404
    body = json_body()
    proposed_rag = body.get("proposed_rag")
    if not proposed_rag:
        return jsonify({"error": "proposed_rag is required"}), 400
    mrc, error = _target_mrc(record)
    if error:
        return error
    raise_signoff(context_from_request(body), AI_SYSTEM_SUBJECT, ai_system_id,
                  kind="rag", proposed_rag=proposed_rag, target_mrc=mrc["value"],
                  note=body.get("note"))
    return jsonify(get_ai_system(ai_system_id)), 201
