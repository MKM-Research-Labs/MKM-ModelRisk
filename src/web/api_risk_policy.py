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

from src.governance.risk_policy import default_policy, get_risk_policy
from src.web._helpers import reference_options

risk_policy_bp = Blueprint("risk_policy", __name__)


@risk_policy_bp.get("/api/risk-policy")
def risk_policy_registry():
    """The seed policy + every division's live policy, keyed by division name."""
    divisions = reference_options().get("division") or []
    return jsonify({
        "seed": default_policy(),
        "divisions": {division: get_risk_policy(division) for division in divisions},
    })
