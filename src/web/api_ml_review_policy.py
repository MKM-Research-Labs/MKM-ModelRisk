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
"""The ML review policy API: what a division's ML review asks for.

Shaped like ``api_risk_policy`` because it is the same journey — an admin edits, the
division's MRC ratifies — and an admin who has set one should not have to learn the
other. The detail response carries the catalogue as well as the policy, so the editor
renders every tickable item without a second call and without knowing that half of
them come from code and half from a reference list.
"""
from __future__ import annotations

from flask import Blueprint, jsonify

from config.governance import item_group_labels
from src.command import dispatch
from src.governance.ml_review_policy import (approve_ml_review_policy, catalogue,
                                             load, propose_ml_review_policy,
                                             reject_ml_review_policy, resolved_policy)
from src.web._helpers import context_from_request, json_body, reference_options
from src.web._ratified_policy_api import (register_ratification_routes,
                                          registry_payload)

ml_review_policy_bp = Blueprint("ml_review_policy", __name__)


def _detail(division: str) -> dict:
    """One division's policy for the Admin editor.

    ``effective`` is what the record screens will actually do — the draft's effect if
    a draft is pending, the live policy's otherwise — so the editor can show the
    consequence of what is being proposed rather than only the stored overrides.
    """
    state = load(division)
    pending = state["draft"] if state["draft"] is not None else state["live"]
    return {
        "division": division,
        "live": state["live"],
        "draft": state["draft"],
        "state": state["state"],
        "approved_at": state["approved_at"],
        "catalogue": catalogue(),
        "groups": item_group_labels(),
        "effective": resolved_policy(division, policy=pending),
    }


@ml_review_policy_bp.get("/api/ml-review-policy")
def ml_review_policy_registry():
    """Every division's lifecycle state, so the tab can show where each one stands."""
    return jsonify(registry_payload(load))


@ml_review_policy_bp.get("/api/ml-review-policy/<division>")
def ml_review_policy_detail(division: str):
    """The catalogue, the live policy, any pending draft, and the effective settings."""
    return jsonify(_detail(division))


@ml_review_policy_bp.post("/api/ml-review-policy/<division>/propose")
def propose_policy_route(division: str):
    """Save the edited policy as a draft for the division's MRC to sign off.

    Nothing on any ML Application changes until it is approved: a draft is a proposal
    about what reviews will ask for, not a change to what they ask for today.
    """
    body = json_body()
    dispatch("propose_ml_review_policy", propose_ml_review_policy,
             context=context_from_request(body),
             division=division, policy=body.get("policy"))
    return jsonify(_detail(division))


register_ratification_routes(
    ml_review_policy_bp, "/api/ml-review-policy",
    approve_command="approve_ml_review_policy", approve=approve_ml_review_policy,
    reject_command="reject_ml_review_policy", reject=reject_ml_review_policy,
    detail=_detail)
