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
"""HTTP routes for an AI System's run evidence."""
from __future__ import annotations

import pytest

from tests.web.conftest import HEADERS

_MIN = {"division": "Risk", "owner": "David K Kelly",
        "use_case": "Drafts the first pass of a credit memo.",
        "deployment_pattern": "Agentic (tool-using)", "ai_autonomy": "SINGLE_CALL"}


def _register(client, ai_system_id):
    client.post("/api/ai-systems", json={"ai_system_id": ai_system_id, "actor": "admin",
                                         "fields": {"name": ai_system_id, **_MIN}},
                headers=HEADERS)
    client.post(f"/api/ai-systems/{ai_system_id}/snapshots", json={"actor": "admin"},
                headers=HEADERS)


def _post(client, path, body):
    return client.post(f"/api/ai-systems/AIS-0001/{path}", headers=HEADERS,
                       json={"actor": "admin", **body})


def test_the_console_is_served_the_evidence_vocabularies(client):
    spec = client.get("/api/ai-systems/fields").get_json()
    assert "Production sample" in spec["trace_purposes"]
    assert "step_graph" in spec["trace_required_content"]["AGENT"]
    assert spec["stress_response_labels"]["RETRY"] == "Retry within budget"
    assert spec["ace_min_samples"] == 20
    cases = next(c for c in spec["collections"] if c["key"] == "stress_test_cases")
    assert any(f["key"] == "expected_response" for f in cases["fields"])


def test_a_trace_is_recorded_and_its_completeness_returned(client):
    _register(client, "AIS-0001")
    res = _post(client, "traces", {"run_id": "R1", "trace_uri": "otel://R1",
                                   "content_hash": "cd" * 32, "contents": ["output"],
                                   "purpose": "Incident"})
    assert res.status_code == 201
    assert res.get_json()["trace"]["complete"] is False


def test_a_stress_run_is_recorded_against_the_register(client):
    _register(client, "AIS-0001")
    client.post("/api/ai-systems/AIS-0001/collections/stress_test_cases", headers=HEADERS,
                json={"actor": "admin", "fields": {
                    "scenario": "Injected instruction", "category": "ADVERSARIAL",
                    "expected_response": "REFUSE_ISOLATE"}})
    case = client.get("/api/ai-systems/AIS-0001").get_json()["data"]["stress_test_cases"][0]
    res = _post(client, "stress-runs", {"occasion": "Before release",
                                        "observed": {case["item_id"]: "REFUSE_ISOLATE"}})
    assert res.status_code == 201 and res.get_json()["run"]["passed"] is True


def test_a_calibration_returns_the_judges_standing(client):
    _register(client, "AIS-0001")
    _register(client, "AIS-JUDGE")
    res = _post(client, "calibrations", {
        "judge_ai_system_id": "AIS-JUDGE", "dimension": "safety",
        "pairs": [{"expert": 5, "judge": 5}] * 20})
    assert res.status_code == 201
    assert res.get_json()["judge_reliance"] == {"AIS-JUDGE": "in force"}


def test_a_refusal_comes_back_as_a_400_with_the_reason(client):
    _register(client, "AIS-0001")
    res = _post(client, "calibrations", {"judge_ai_system_id": "AIS-JUDGE",
                                         "dimension": "safety", "pairs": []})
    assert res.status_code == 400
    assert "not a registered AI System" in res.get_json()["error"]


@pytest.mark.parametrize("path", ["traces", "stress-runs", "calibrations"])
def test_an_unknown_system_is_a_404(client, path):
    assert _post(client, path, {}).status_code == 404
