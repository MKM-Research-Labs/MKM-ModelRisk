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

from flask import Blueprint, jsonify

from src.command import dispatch
from src.governance.risk_policy import default_policy, get_risk_policy, load, propose_policy
from src.web._helpers import context_from_request, json_body, reference_options

risk_policy_bp = Blueprint("risk_policy", __name__)


@risk_policy_bp.get("/api/risk-policy")
def risk_policy_registry():
    """The seed policy + every division's live policy, keyed by division name."""
    divisions = reference_options().get("division") or []
    return jsonify({
        "seed": default_policy(),
        "divisions": {division: get_risk_policy(division) for division in divisions},
    })


@risk_policy_bp.get("/api/risk-policy/<division>")
def risk_policy_detail(division: str):
    """One division's policy for the Admin editor: its live (approved) policy, any draft
    awaiting MRC sign-off, and the lifecycle state (seed / draft / approved)."""
    state = load(division)
    return jsonify({"division": division, "live": state["live"], "draft": state["draft"],
                    "state": state["state"], "seed": default_policy()})


@risk_policy_bp.post("/api/risk-policy/<division>/propose")
def propose_risk_policy(division: str):
    """Save a division's edited policy as a draft for its MRC to sign off. The draft does
    not affect any model until approved at the division's MRC meeting."""
    body = json_body()
    dispatch("propose_risk_policy", propose_policy, context=context_from_request(body),
             division=division, policy=body.get("policy"))
    state = load(division)
    return jsonify({"division": division, "live": state["live"], "draft": state["draft"],
                    "state": state["state"]})
