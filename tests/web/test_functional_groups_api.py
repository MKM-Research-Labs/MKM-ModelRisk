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
"""The functional-group HTTP API: what the Admin editor draws and the MRC ratifies."""
from __future__ import annotations

from tests.web.conftest import HEADERS

DIV = "PhysicalRisk"
STORM = {"name": "Storm Generation", "description": "Hazard generation."}
FLOOD = {"name": "Flood Simulation"}


def _propose(client, groups, division=DIV):
    return client.post(f"/api/functional-groups/{division}/propose",
                       json={"groups": groups, "confirmed": True}, headers=HEADERS)


def _approve(client, division=DIV, meeting_id=None):
    return client.post(f"/api/functional-groups/{division}/approve",
                       json={"meeting_id": meeting_id, "confirmed": True},
                       headers=HEADERS)


def test_a_division_starts_with_no_list_and_says_so(client):
    body = client.get(f"/api/functional-groups/{DIV}").get_json()
    assert set(body) == {"division", "live", "draft", "state", "approved_at", "in_use"}
    assert body["live"] == [] and body["draft"] is None
    assert body["state"] == "seed"


def test_proposing_returns_the_draft_with_ids_the_editor_did_not_have_to_invent(client):
    body = _propose(client, [STORM, FLOOD]).get_json()
    assert body["state"] == "draft"
    assert [g["id"] for g in body["draft"]] == ["FG-001", "FG-002"]
    assert body["live"] == [], "a proposal is not a decision"


def test_approving_makes_the_draft_live(client):
    _propose(client, [STORM])
    body = _approve(client, meeting_id="MRC-PR-Q1").get_json()
    assert body["state"] == "approved"
    assert body["draft"] is None
    assert [g["name"] for g in body["live"]] == ["Storm Generation"]
    assert body["approved_at"], "the ratification date is the evidence"


def test_rejecting_leaves_the_live_list_alone(client):
    _propose(client, [STORM])
    _approve(client)
    _propose(client, [STORM, FLOOD])
    body = client.post(f"/api/functional-groups/{DIV}/reject",
                       json={"confirmed": True}, headers=HEADERS).get_json()
    assert body["state"] == "approved"
    assert [g["name"] for g in body["live"]] == ["Storm Generation"]


def test_a_malformed_list_is_refused_rather_than_stored(client):
    res = _propose(client, [{"name": "Storm"}, {"name": "storm"}])
    assert res.status_code == 400
    assert "both named" in res.get_json()["error"]
    assert client.get(f"/api/functional-groups/{DIV}").get_json()["state"] == "seed"


def test_the_registry_carries_every_divisions_list_and_state(client):
    # The registry enumerates the admin DIVISION list, exactly as the risk-policy and
    # ML-review-policy registries do, so a division has to exist there to appear.
    client.post("/api/reference/collections/division",
                json={"fields": {"value": DIV}, "confirmed": True}, headers=HEADERS)
    _propose(client, [STORM])
    _approve(client)
    reg = client.get("/api/functional-groups").get_json()
    assert set(reg) == {"divisions", "states"}
    assert [g["name"] for g in reg["divisions"][DIV]] == ["Storm Generation"]
    assert reg["states"][DIV]["state"] == "approved"
    for state in reg["states"].values():
        assert set(state) == {"state", "approved_at"}


def test_in_use_counts_what_a_removal_would_cost_before_it_is_attempted(client):
    _propose(client, [STORM])
    _approve(client)
    client.post("/api/models", json={"model_id": "M1", "name": "Alpha",
                                     "fields": {"division": DIV}, "confirmed": True},
                headers=HEADERS)
    client.post("/api/models/M1/field",
                json={"field": "functional_group", "value": "FG-001",
                      "confirmed": True}, headers=HEADERS)
    body = client.get(f"/api/functional-groups/{DIV}").get_json()
    assert body["in_use"] == {"FG-001": 1}
    # ...and the domain refuses the removal the editor was warning about.
    res = _propose(client, [])
    assert res.status_code == 400
    assert "cannot be removed" in res.get_json()["error"]
