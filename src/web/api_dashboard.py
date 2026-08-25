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
"""The dashboard API: the landing tab's whole payload in one read.

Read-only, and deliberately so. The dashboard has no acknowledge and no dismiss:
an executive clearing an item from a screen would be an ungoverned decision with
no minute attached to it, and the platform's premise is that a response is
recorded where it can be challenged. This endpoint routes the reader to the
record or the committee; it never settles anything itself.

One request rather than two. The design sketched a fast first paint from the
projections with the completeness figures filling in behind, but the response rule
itself depends on the completeness scan — a record below its division's standard is
one of the three limbs — so a first paint without it would show a verdict that
could flip from "no" to "yes" a second later. A verdict that changes under the
reader is worse than a verdict that takes a moment.

The state vocabulary travels with the payload. Every label on the screen is an
adopter's to re-set (``config.governance._attention``), so no state name is written
into a ``.js`` file — the same rule the theme API already enforces for colour.
"""
from __future__ import annotations

from flask import Blueprint, jsonify, request

from config.governance import (
    ATTENTION_STATES,
    ATTENTION_STATE_CARD,
    ATTENTION_STATE_LABELS,
    ATTENTION_STATE_RESPONSE,
    RESPONSE_STATES,
)
from src.governance.attention import dashboard

dashboard_bp = Blueprint("dashboard", __name__)


def state_vocabulary() -> list[dict]:
    """The four states as the screen shows them: worst first, each with the label
    and the instruction the adopter has configured for it."""
    return [{
        "state": state,
        "label": ATTENTION_STATE_LABELS.get(state, state),
        "card": ATTENTION_STATE_CARD.get(state, state),
        "response": ATTENTION_STATE_RESPONSE.get(state, ""),
        "needs_response": state in RESPONSE_STATES,
    } for state in ATTENTION_STATES]


@dashboard_bp.get("/api/dashboard")
def get_dashboard():
    """Everything the landing tab draws.

    ``as_of`` is accepted so a reader can ask what the page said on a given date
    against today's register — useful when a committee paper quotes a figure. It
    does not replay history: the registers hold current state, and only the dated
    rules (review currency, remediation dates) move with it.
    """
    as_of = (request.args.get("as_of") or "").strip() or None
    payload = dashboard(as_of)
    payload["states"] = state_vocabulary()
    return jsonify(payload)
