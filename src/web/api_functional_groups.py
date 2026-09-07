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
"""The functional-group API: how a division carves its estate up, and who agreed it.

Shaped like ``api_ml_review_policy`` because it is the same journey -- an admin
edits, the division's MRC ratifies -- and an administrator who has set one should
not have to learn the other.

The registry is what the console loads once at startup, the way it already loads
the risk policies: every division's live list in one call, resolved client-side by
a record's division. Making the per-register ``/fields`` endpoints division-aware
instead would mean a spec that varies by record, which those endpoints are not
built to be.
"""
from __future__ import annotations

from flask import Blueprint, jsonify

from src.command import dispatch
from src.governance.functional_groups import (approve_functional_groups,
                                              groups_in_use, load,
                                              propose_functional_groups,
                                              reject_functional_groups)
from src.web._helpers import context_from_request, json_body, reference_options
from src.web._ratified_policy_api import (register_ratification_routes,
                                          registry_payload)

functional_groups_bp = Blueprint("functional_groups", __name__)


def _detail(division: str) -> dict:
    """One division's list for the Admin editor and the meeting's sign-off item.

    ``in_use`` counts the live records filed under each group, so the editor can say
    what removing one would cost before an administrator tries it -- the domain
    refuses the removal either way, but a count beside the row is an explanation and
    a refusal afterwards is a surprise.
    """
    state = load(division)
    return {
        "division": division,
        "live": state["live"],
        "draft": state["draft"],
        "state": state["state"],
        "approved_at": state["approved_at"],
        "in_use": {group_id: len(records)
                   for group_id, records in groups_in_use(division).items()},
    }


@functional_groups_bp.get("/api/functional-groups")
def functional_groups_registry():
    """Every division's live list and its lifecycle state, keyed by division."""
    return jsonify(registry_payload(load))


@functional_groups_bp.get("/api/functional-groups/<division>")
def functional_groups_detail(division: str):
    """The live list, any pending draft, and how many records hold each group."""
    return jsonify(_detail(division))


@functional_groups_bp.post("/api/functional-groups/<division>/propose")
def propose_groups_route(division: str):
    """Save the edited list as a draft for the division's MRC to sign off.

    No record moves until it is approved. A proposal that would drop a group records
    are still filed under is refused here rather than at the meeting.
    """
    body = json_body()
    dispatch("propose_functional_groups", propose_functional_groups,
             context=context_from_request(body),
             division=division, groups=body.get("groups"))
    return jsonify(_detail(division))


register_ratification_routes(
    functional_groups_bp, "/api/functional-groups",
    approve_command="approve_functional_groups", approve=approve_functional_groups,
    reject_command="reject_functional_groups", reject=reject_functional_groups,
    detail=_detail)
