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
"""HTTP API for the change register.

The endpoint set is one for all three record types, so most of what is worth asserting
here is about the seam: that a proposal cannot be filed against a record that does not
exist, and that the starting point a tier is derived from comes from the record rather
than from the request.
"""
from __future__ import annotations

from config.governance._change import CHANGE_CLASSES
from tests.web.conftest import HEADERS

_AI_SYSTEM = {"name": "Client mail summariser", "division": "Risk",
              "owner": "David K Kelly",
              "use_case": "Summarises inbound client correspondence for the desk.",
              "deployment_pattern": "Agentic (tool-using)",
              "foundation_model": "claude-opus-4"}


def _register_ai_system(client, ai_system_id="AIS-0001", **overrides):
    return client.post("/api/ai-systems", json={
        "ai_system_id": ai_system_id, "fields": {**_AI_SYSTEM, **overrides},
        "actor": "admin"}, headers=HEADERS)


def _propose(client, **overrides):
    body = {"subject_type": "ai_system", "subject_id": "AIS-0001",
            "rationale": "Provider has deprecated the pinned version",
            "after": {"foundation_model": "claude-opus-5"}}
    body.update(overrides)
    return client.post("/api/changes", json=body, headers=HEADERS)


def test_change_against_unknown_subject_404s(client):
    """And creates no aggregate: an id typed wrong would leave a proposal pointing at
    nothing, and the log cannot take it back."""
    res = _propose(client, subject_id="AIS-9999")
    assert res.status_code == 404
    assert "not found" in res.get_json()["error"]
    assert client.get("/api/changes").get_json() == []


def test_change_against_unknown_record_type_404s(client):
    res = _propose(client, subject_type="teapot")
    assert res.status_code == 404
    assert "unknown record type" in res.get_json()["error"]
    assert client.get("/api/changes").get_json() == []


def test_propose_classify_and_read_back(client):
    _register_ai_system(client)
    created = _propose(client)
    assert created.status_code == 201
    change_id = created.get_json()["change_id"]

    classified = client.post(f"/api/changes/{change_id}/classify",
                             json={"actor": "admin"}, headers=HEADERS).get_json()
    assert classified["data"]["change_class"] == "Material"
    assert classified["data"]["revalidation_depth"] == "rebaseline"


def test_before_is_read_from_the_record_not_the_request(client):
    """A caller cannot pick its own tier by misdescribing where the record started.

    Here the request claims the system already runs on ``claude-opus-5``, which would
    make the proposal a no-op. The recorded ``before`` is what the record actually
    holds, so the change classifies on its real movement.
    """
    _register_ai_system(client)
    created = _propose(client, before={"foundation_model": "claude-opus-5"})
    data = created.get_json()["data"]
    assert data["before"] == {"foundation_model": "claude-opus-4"}

    change_id = created.get_json()["change_id"]
    classified = client.post(f"/api/changes/{change_id}/classify",
                             json={"actor": "admin"}, headers=HEADERS).get_json()
    assert classified["data"]["change_class"] == "Material"


def test_ids_are_minted_in_sequence(client):
    _register_ai_system(client)
    first = _propose(client).get_json()["change_id"]
    second = _propose(client).get_json()["change_id"]
    assert (first, second) == ("CHG-001", "CHG-002")


def test_the_register_narrows_to_one_record(client):
    _register_ai_system(client)
    _register_ai_system(client, ai_system_id="AIS-0002")
    _propose(client)
    _propose(client, subject_id="AIS-0002")

    rows = client.get("/api/changes?subject_type=ai_system&subject_id=AIS-0002")
    assert [r["change_id"] for r in rows.get_json()] == ["CHG-002"]


def test_superseding_drops_a_proposal_from_the_open_register(client):
    _register_ai_system(client)
    change_id = _propose(client).get_json()["change_id"]
    res = client.post(f"/api/changes/{change_id}/supersede", json={"actor": "admin"},
                      headers=HEADERS)
    assert res.get_json()["data"]["superseded"] is True
    assert client.get("/api/changes?open=1").get_json() == []
    assert len(client.get("/api/changes").get_json()) == 1


def test_a_missing_change_404s(client):
    assert client.get("/api/changes/CHG-404").status_code == 404


def test_a_domain_refusal_is_a_400(client):
    _register_ai_system(client)
    change_id = _propose(client).get_json()["change_id"]
    client.post(f"/api/changes/{change_id}/classify", json={"actor": "admin"},
                headers=HEADERS)
    again = client.post(f"/api/changes/{change_id}/classify", json={"actor": "admin"},
                        headers=HEADERS)
    assert again.status_code == 400
    assert "already classified" in again.get_json()["error"]


def test_the_vocabulary_is_served_so_no_screen_carries_its_own_copy(client):
    body = client.get("/api/changes/vocabulary").get_json()
    assert body["change_classes"] == list(CHANGE_CLASSES)
    assert body["subject_workflows"]["ai_system"] == "ai"
    assert body["depth_matrix"]["Material"]["ai"] == "rebaseline"
    assert body["depth_matrix"]["Material"]["ml"] == "validation_pack_refresh"
    assert set(body["class_notes"]) == set(CHANGE_CLASSES)
