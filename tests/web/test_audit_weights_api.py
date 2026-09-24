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
"""Criticality weights end to end: offered by the editor, ratified, then scored.

The unit tests (tests/governance/test_completeness_weights.py) prove the arithmetic
on a policy handed to the audit directly. These prove the path a committee takes:
the editor is offered only names the validator accepts, a weight survives propose
and approve, and the audit reads it only once it is approved.
"""
from __future__ import annotations

from config.governance import FIELD_CRITICALITY
from src.governance.completeness.weight_catalogue import weight_catalogue
from src.governance.model_inventory.risk import compute_risk_rating
from src.governance.risk_policy.commands import _validate_policy
from src.governance.risk_policy import default_policy
from tests.web.conftest import HEADERS

AS_OF = "2026-09-24"


def test_the_editor_is_offered_only_names_the_committee_can_ratify():
    """Every row the Audit tab lists must pass the validator at both bounds, or an
    administrator could enter a weight the proposal would then refuse."""
    catalogue = weight_catalogue()
    for section in catalogue["sections"]:
        for bound in (catalogue["min"], catalogue["max"]):
            policy = default_policy()
            policy["audit"][section["policy_key"]] = {r["name"]: bound for r in section["rows"]}
            _validate_policy(policy)


def test_the_editor_shows_labels_and_firm_wide_values():
    fields = weight_catalogue()["sections"][0]
    owner = next(r for r in fields["rows"] if r["name"] == "owner")
    assert fields["policy_key"] == "field_weights"
    assert owner == {"name": "owner", "label": "Owner", "firm": FIELD_CRITICALITY["owner"]}


def test_the_division_detail_carries_the_catalogue(client):
    detail = client.get("/api/risk-policy/AnyDivision").get_json()
    assert detail["audit_weights"] == weight_catalogue()


def _propose_weight(client, division, weight):
    policy = client.get(f"/api/risk-policy/{division}").get_json()["seed"]
    policy["audit"]["field_weights"] = {"owner": weight}
    return client.post(f"/api/risk-policy/{division}/propose",
                       json={"policy": policy, "confirmed": True}, headers=HEADERS)


def _scored_on(division):
    return compute_risk_rating({"division": division}, as_of=AS_OF)["audit_policy"]


def test_a_weight_is_scored_only_once_the_committee_approves_it(client):
    div = "WeightsDiv"
    assert _propose_weight(client, div, 1.9).status_code == 200
    # A draft sits with the MRC; the audit still scores the division on the seed.
    assert _scored_on(div).get("field_weights") == {}
    client.post(f"/api/risk-policy/{div}/approve",
                json={"meeting_id": "MTG-WEIGHTS", "confirmed": True}, headers=HEADERS)
    assert _scored_on(div)["field_weights"] == {"owner": 1.9}


def test_a_weight_below_the_floor_is_refused_over_the_api(client):
    resp = _propose_weight(client, "FloorDiv", 0.05)
    assert resp.status_code == 400
    assert "must be a number from 0.10 to 2.00" in resp.get_json()["error"]
