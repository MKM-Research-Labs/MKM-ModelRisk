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
"""What the console is served for an AI System's classification and grid position."""
from __future__ import annotations

from tests.web.conftest import HEADERS

_MINIMUM = {"name": "Credit memo drafter", "division": "Risk", "owner": "David K Kelly",
            "use_case": "Drafts the first pass of a credit memo from the file.",
            "deployment_pattern": "Agentic (tool-using)"}


def _fields(client):
    spec = client.get("/api/ai-systems/fields").get_json()
    return spec, {f["key"]: f for g in spec["groups"] for f in g["fields"]}


def test_the_class_is_served_as_immutable_with_its_labels(client):
    _, fields = _fields(client)
    assert fields["model_class"]["immutable"] is True
    assert fields["ai_autonomy"]["option_labels"]["AGENT"].startswith("AI agent")
    assert "immutable" not in fields["ai_autonomy"]


def test_the_complexity_fields_are_offered_at_registration_but_not_demanded(client):
    spec, _ = _fields(client)
    for key in ("ai_system_type", "ai_autonomy", "ai_usage_frequency"):
        assert key in spec["register_optional"]
        assert key not in spec["register"]
    assert "model_class" not in spec["register"] + spec["register_optional"]


def test_a_read_carries_the_grid_position(client):
    client.post("/api/ai-systems", json={
        "ai_system_id": "AIS-0001", "actor": "admin",
        "fields": {**_MINIMUM, "materiality": "Low", "ai_autonomy": "SINGLE_CALL",
                   "ai_usage_frequency": "AD_HOC"}}, headers=HEADERS)
    body = client.get("/api/ai-systems/AIS-0001").get_json()
    assert body["data"]["model_class"] == "AI_SYSTEM"
    assert body["grid"]["position"] == "Low × Low"
    assert body["grid"]["intensity"] == "Baseline"
    assert client.get("/api/ai-systems").get_json()[0]["grid"]["placed"] is True


def test_editing_the_class_over_http_is_refused(client):
    client.post("/api/ai-systems", json={"ai_system_id": "AIS-0001", "actor": "admin",
                                         "fields": _MINIMUM}, headers=HEADERS)
    res = client.post("/api/ai-systems/AIS-0001/field", headers=HEADERS,
                      json={"field": "model_class", "value": "ML_APP", "actor": "admin"})
    assert res.status_code == 400
    assert "cannot be edited" in res.get_json()["error"]
