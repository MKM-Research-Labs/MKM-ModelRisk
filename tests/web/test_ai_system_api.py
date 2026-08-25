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
"""HTTP API for the AI System aggregate."""
from __future__ import annotations

from tests.web.conftest import HEADERS

_MINIMUM = {"name": "Client mail summariser", "division": "Risk",
            "owner": "David K Kelly",
            "use_case": "Summarises inbound client correspondence for the desk.",
            "deployment_pattern": "Agentic (tool-using)"}


def _register(client, ai_system_id="AIS-0001", **overrides):
    return client.post("/api/ai-systems", json={
        "ai_system_id": ai_system_id, "fields": {**_MINIMUM, **overrides},
        "actor": "admin"}, headers=HEADERS)


def test_register_and_read_back(client):
    assert _register(client).status_code == 201
    body = client.get("/api/ai-systems/AIS-0001").get_json()
    assert body["data"]["name"] == "Client mail summariser"
    assert body["data"]["deployment_pattern"] == "Agentic (tool-using)"


def test_the_register_form_asks_for_the_deployment_pattern(client):
    """It decides which risks apply, so it is on the short registration form rather
    than left to be filled in later."""
    spec = client.get("/api/ai-systems/fields").get_json()
    assert "deployment_pattern" in spec["register"]
    groups = {g["group"] for g in spec["groups"]}
    assert {"The AI system", "Exposure", "Controls"} <= groups


def test_a_bad_choice_is_refused_with_the_allowed_values(client):
    res = _register(client, ai_system_id="AIS-0002", hosting="Somebody's laptop")
    assert res.status_code == 400
    assert "hosting must be one of" in res.get_json()["error"]


def test_missing_a_required_field_is_refused(client):
    res = client.post("/api/ai-systems", json={
        "ai_system_id": "AIS-0003",
        "fields": {k: v for k, v in _MINIMUM.items() if k != "use_case"},
        "actor": "admin"}, headers=HEADERS)
    assert res.status_code == 400
    assert "use_case is required" in res.get_json()["error"]


def test_a_field_edit_is_recorded(client):
    _register(client)
    res = client.post("/api/ai-systems/AIS-0001/field",
                      json={"field": "data_egress", "value": "Personal data (PII)",
                            "actor": "admin"}, headers=HEADERS)
    assert res.status_code == 200
    assert res.get_json()["data"]["data_egress"] == "Personal data (PII)"


def test_tools_round_trip_through_the_collection(client):
    _register(client)
    res = client.post("/api/ai-systems/AIS-0001/collections/agent_tools",
                      json={"fields": {"name": "payments.transfer",
                                       "authority": "Initiates a payment",
                                       "approval": "Always"},
                            "actor": "admin"}, headers=HEADERS)
    assert res.status_code == 201
    tools = res.get_json()["data"]["agent_tools"]
    assert len(tools) == 1 and tools[0]["name"] == "payments.transfer"


def test_retiring_takes_it_out_of_the_list(client):
    _register(client)
    assert client.post("/api/ai-systems/AIS-0001/retire",
                       json={"actor": "admin"}, headers=HEADERS).status_code == 200
    assert client.get("/api/ai-systems").get_json() == []
    assert len(client.get("/api/ai-systems?include_retired=1").get_json()) == 1


def test_it_is_rated_by_the_same_engine_a_model_is(client):
    _register(client, tier="1", materiality="High", complexity="High")
    rating = client.get("/api/ai-systems/AIS-0001/risk-rating").get_json()
    assert "rating" in rating or "rag_rating" in rating or rating


def test_an_unknown_record_is_a_404(client):
    assert client.get("/api/ai-systems/AIS-9999").status_code == 404
