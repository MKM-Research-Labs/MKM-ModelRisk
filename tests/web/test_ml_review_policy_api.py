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
"""The ML review policy HTTP API: the catalogue the editor draws, and ratification."""
from __future__ import annotations

from config.governance import TRAINING_ITEM_SOURCE, policy_item_id
from src.governance.reference import ensure_default_estimators
from tests.web._signoff_flows import _seed_mrc
from tests.web.conftest import HEADERS

DIV = "PhysicalRisk"
LEARNING_TASK = policy_item_id(TRAINING_ITEM_SOURCE, "learning_task")


def _propose(client, policy, division=DIV):
    return client.post(f"/api/ml-review-policy/{division}/propose",
                       json={"policy": policy, "confirmed": True}, headers=HEADERS)


def test_detail_carries_the_catalogue_so_the_editor_needs_one_call(client):
    body = client.get(f"/api/ml-review-policy/{DIV}").get_json()
    assert set(body) >= {"division", "live", "draft", "state", "catalogue",
                         "groups", "effective"}
    assert body["state"] == "seed"
    assert len(body["catalogue"]) == len(body["effective"])
    # Every group heading the catalogue uses is one the editor can render.
    assert {item["group"] for item in body["catalogue"]} <= set(body["groups"])


def test_effective_shows_what_the_draft_would_do_before_it_is_ratified(client):
    res = _propose(client, {LEARNING_TASK: {"in_use": True, "mandatory": True}})
    assert res.status_code == 200
    body = res.get_json()
    assert body["state"] == "draft"
    # The editor shows the consequence of the proposal...
    assert body["effective"][LEARNING_TASK] == {"in_use": True, "mandatory": True}
    # ...while the live policy, which records are judged against, is untouched.
    assert body["live"] == {}


def test_approving_makes_the_draft_live(client):
    _propose(client, {LEARNING_TASK: {"in_use": True, "mandatory": True}})
    body = client.post(f"/api/ml-review-policy/{DIV}/approve",
                       json={"meeting_id": "MRC-PR-Q1", "confirmed": True},
                       headers=HEADERS).get_json()
    assert body["state"] == "approved"
    assert body["draft"] is None
    assert body["live"][LEARNING_TASK]["mandatory"] is True


def test_rejecting_leaves_the_live_policy_alone(client):
    _propose(client, {LEARNING_TASK: {"in_use": True, "mandatory": True}})
    client.post(f"/api/ml-review-policy/{DIV}/approve",
                json={"confirmed": True}, headers=HEADERS)
    _propose(client, {})
    body = client.post(f"/api/ml-review-policy/{DIV}/reject",
                       json={"confirmed": True}, headers=HEADERS).get_json()
    assert body["state"] == "approved"
    assert body["live"][LEARNING_TASK]["mandatory"] is True


def test_a_policy_the_committee_should_never_see_is_refused(client):
    """Mandatory while not in use — the domain rule, reached through the API."""
    res = _propose(client, {LEARNING_TASK: {"in_use": False, "mandatory": True}})
    assert res.status_code == 400
    assert "cannot be mandatory while it is not in use" in res.get_json()["error"]


def test_the_registry_lists_every_divisions_state(client):
    reg = client.get("/api/ml-review-policy").get_json()
    assert set(reg) == {"divisions", "states"}
    for state in reg["states"].values():
        assert set(state) == {"state", "approved_at"}


# --- The gate, reached through the API ---------------------------------------

def _ratify(client, policy):
    client.post(f"/api/ml-review-policy/{DIV}/propose",
                json={"policy": policy, "confirmed": True}, headers=HEADERS)
    client.post(f"/api/ml-review-policy/{DIV}/approve",
                json={"confirmed": True}, headers=HEADERS)


def _register_ml(client):
    ensure_default_estimators()
    _seed_mrc(client)          # something has to be there to route the request to
    client.post("/api/ml-applications",
                json={"ml_application_id": "MLA-0001", "confirmed": True,
                      "fields": {"name": "Retail PD", "division": DIV,
                                 "owner": "David K Kelly",
                                 "estimator": "GradientBoostingClassifier",
                                 "use_case": "Ranks applicants by PD."}},
                headers=HEADERS)
    client.post("/api/ml-applications/MLA-0001/collections/training_runs",
                json={"fields": {"fit_id": "1.0"}, "confirmed": True}, headers=HEADERS)


def test_a_record_carries_what_its_division_asks_of_it(client):
    _ratify(client, {policy_item_id(TRAINING_ITEM_SOURCE, "intended_use"):
                     {"in_use": True, "mandatory": True}})
    _register_ml(client)
    scope = client.get("/api/ml-applications/MLA-0001").get_json()["review_scope"]
    assert scope["missing_mandatory"] == ["Intended use"]


def test_the_committee_is_not_asked_to_sign_off_an_unfinished_review(client):
    _ratify(client, {policy_item_id(TRAINING_ITEM_SOURCE, "intended_use"):
                     {"in_use": True, "mandatory": True}})
    _register_ml(client)
    res = client.post("/api/ml-applications/MLA-0001/request-signoff",
                      json={"proposed_rag": "Green", "confirmed": True}, headers=HEADERS)
    assert res.status_code == 400
    assert "Intended use" in res.get_json()["error"]
