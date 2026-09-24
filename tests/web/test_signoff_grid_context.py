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
"""An AI System's grid position travels to its committee; it never chooses the committee.

Spec v0.5 §3.3 (AIGov edition) names grid position a routing input. §11b of the plan
removed routing on a record's attributes on 2026-09-06, and on 2026-09-24 the user chose
that the position travel WITH the request instead. So these tests assert both halves:
the request and its agenda item carry the position, and two systems at opposite ends of
the grid still go to the same committee.
"""
from __future__ import annotations

from src.governance.ai_system.committee_context import committee_context
from tests.web._signoff_flows import (_schedule_meeting, _seed_mrc, decide,
                                      signoff_item_of_kind)
from tests.web.conftest import HEADERS
from tests.web.test_mrc_retire_aiml_api import register_ai, register_ml

_HIGH = {"materiality": "High", "ai_autonomy": "AGENT", "ai_usage_frequency": "CONTINUOUS"}
_LOW = {"materiality": "Low", "ai_autonomy": "SINGLE_CALL", "ai_usage_frequency": "AD_HOC"}


def _propose(client, path, record_id):
    return client.post(f"{path}/{record_id}/request-signoff", headers=HEADERS,
                       json={"proposed_rag": "Green", "confirmed": True})


def _request(client, path, record_id):
    return client.get(f"{path}/{record_id}").get_json()["data"]["signoff_requests"][-1]


def test_the_request_and_its_agenda_item_carry_the_grid(client):
    _seed_mrc(client)
    register_ai(client, **_HIGH)
    _schedule_meeting(client)
    assert _propose(client, "/api/ai-systems", "AIS-0001").status_code == 201
    request = _request(client, "/api/ai-systems", "AIS-0001")
    assert request["grid_position"] == "High × High"
    assert request["governance_intensity"] == "Intensive"
    assert "robustness: not evidenced" in request["property_coverage"]
    item = signoff_item_of_kind(client, "rag")
    for key in ("grid_position", "governance_intensity", "property_coverage"):
        assert item[key] == request[key]


def test_opposite_ends_of_the_grid_go_to_the_same_committee(client):
    """The §11b guard: an Intensive system is not escalated anywhere."""
    _seed_mrc(client)
    register_ai(client, "AIS-HIGH", **_HIGH)
    register_ai(client, "AIS-LOW", **_LOW)
    _propose(client, "/api/ai-systems", "AIS-HIGH")
    _propose(client, "/api/ai-systems", "AIS-LOW")
    high = _request(client, "/api/ai-systems", "AIS-HIGH")
    low = _request(client, "/api/ai-systems", "AIS-LOW")
    assert high["governance_intensity"] == "Intensive"
    assert low["governance_intensity"] == "Baseline"
    assert high["target_mrc"] == low["target_mrc"] == "MRC-CO"


def test_an_unplaced_system_says_what_it_is_missing(client):
    _seed_mrc(client)
    register_ai(client)
    _propose(client, "/api/ai-systems", "AIS-0001")
    request = _request(client, "/api/ai-systems", "AIS-0001")
    assert request["grid_position"].startswith("Not placed — missing")
    assert request["governance_intensity"] == ""


def test_other_record_types_carry_nothing_extra(client):
    _seed_mrc(client)
    register_ml(client)
    _propose(client, "/api/ml-applications", "MLA-0001")
    request = _request(client, "/api/ml-applications", "MLA-0001")
    assert "grid_position" not in request


def test_the_position_the_committee_saw_is_not_rewritten(client):
    """Immutable on the request: the minute has to say what was put to the committee."""
    _seed_mrc(client)
    register_ai(client, **_LOW)
    _propose(client, "/api/ai-systems", "AIS-0001")
    request = _request(client, "/api/ai-systems", "AIS-0001")
    res = client.post(f"/api/ai-systems/AIS-0001/collections/signoff_requests/"
                     f"{request['item_id']}", headers=HEADERS,
                     json={"fields": {"grid_position": "Low × Low (edited)"},
                           "confirmed": True})
    assert res.status_code == 400
    assert "cannot be changed once set" in res.get_json()["error"]


def test_a_decision_on_a_grid_carrying_item_still_goes_through(client):
    """The committee's own writes to the item and the request must not trip on the
    immutable fields they carry."""
    _seed_mrc(client)
    register_ai(client, **_HIGH)
    _schedule_meeting(client)
    _propose(client, "/api/ai-systems", "AIS-0001")
    res = decide(client, signoff_item_of_kind(client, "rag")["item_id"])
    assert res.status_code == 200
    assert res.get_json()["ai_system"]["data"]["rag_rating"] == "Green"


def test_the_summary_reads_the_row_it_is_given():
    assert committee_context(None) == {"grid_position": "", "governance_intensity": "",
                                       "property_coverage": ""}
    row = {"grid": {"placed": True, "position": "Low × Low", "intensity": "Baseline"},
           "coverage": {"properties": {"correctness": {"status": "rests on live evidence",
                                                       "gaps": []}}}}
    assert committee_context(row)["property_coverage"] == \
        "correctness: rests on live evidence"
