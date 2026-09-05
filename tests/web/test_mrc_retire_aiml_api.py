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
"""The committee ratifies hibernation for an AI System and an ML Application.

The model journey is tested in ``test_mrc_retire_api``. These two record types went
live with a Danger tab that POSTed straight to a retire endpoint, so the one decision
the committee exists to take was the one their owners could take alone. They now take
the model's route, and this is the test of that — walked end to end for both, because
"it reuses the shared machinery" is a claim about wiring and this is the claim about
behaviour.
"""
from __future__ import annotations

from src.governance.reference import ensure_default_estimators
from src.web._signoff_subject import AI_SYSTEM_SUBJECT, ML_APPLICATION_SUBJECT
from tests.web._signoff_flows import (
    _schedule_meeting,
    _seed_mrc,
    decide,
    request_reactivate,
    request_retire,
    signoff_item_of_kind,
)
from tests.web.conftest import HEADERS

_AI = "/api/ai-systems"
_ML = "/api/ml-applications"

_AI_FIELDS = {"name": "Client mail summariser", "division": "Risk",
              "owner": "David K Kelly",
              "use_case": "Summarises inbound client correspondence for the desk.",
              "deployment_pattern": "Agentic (tool-using)"}
_ML_FIELDS = {"name": "Retail PD scorecard", "division": "Risk", "owner": "Dana",
              "estimator": "GradientBoostingClassifier",
              "use_case": "Ranks applicants by PD."}


def register_ai(client, ai_system_id="AIS-0001", **overrides):
    return client.post(_AI, json={"ai_system_id": ai_system_id,
                                  "fields": {**_AI_FIELDS, **overrides},
                                  "confirmed": True}, headers=HEADERS)


def register_ml(client, ml_application_id="MLA-0001", **overrides):
    ensure_default_estimators()
    return client.post(_ML, json={"ml_application_id": ml_application_id,
                                  "fields": {**_ML_FIELDS, **overrides},
                                  "confirmed": True}, headers=HEADERS)


def _ready(client, register, record_id, api):
    """A committee, a record, and a meeting for it to be decided at."""
    _seed_mrc(client)
    register(client)
    _schedule_meeting(client)
    return client.get(f"{api}/{record_id}").get_json()


# --- Both subjects can carry both halves of hibernation -----------------------


def test_both_subjects_carry_retire_and_reactivate():
    """``supports`` is what stops the committee being offered a decision the subject
    cannot carry out, so it is the wiring worth asserting directly."""
    for subject in (AI_SYSTEM_SUBJECT, ML_APPLICATION_SUBJECT):
        assert subject.supports("retire")
        assert subject.supports("reactivate")


# --- AI System ----------------------------------------------------------------


def test_requesting_retire_of_an_ai_system_does_not_hibernate_it(client):
    """The governance guarantee: asking is not deciding."""
    _ready(client, register_ai, "AIS-0001", _AI)
    assert request_retire(client, "AIS-0001", api=_AI).status_code == 201
    record = client.get(f"{_AI}/AIS-0001").get_json()
    assert record["retired"] is False, "it must stay active until ratified"
    request = record["data"]["signoff_requests"][0]
    assert request["kind"] == "retire" and request["status"] == "Attached"
    assert signoff_item_of_kind(client, "retire")["subject_ai_system_id"] == "AIS-0001"


def test_the_committee_hibernates_an_ai_system_and_can_bring_it_back(client):
    _ready(client, register_ai, "AIS-0001", _AI)
    request_retire(client, "AIS-0001", api=_AI)
    payload = decide(client, signoff_item_of_kind(client, "retire")["item_id"]).get_json()
    assert payload["ai_system"]["retired"] is True
    history = payload["ai_system"]["data"]["signoff_history"]
    assert history[-1]["kind"] == "retire" and history[-1]["outcome"] == "Approved"
    # A retire is not a rating decision, so it must not stamp the rating fields.
    assert not payload["ai_system"]["data"].get("mrc_signoff_meeting")

    # A hibernated record is read-only but can still raise this one request —
    # otherwise there is no way back.
    assert request_reactivate(client, "AIS-0001", api=_AI).status_code == 201
    back = decide(client, signoff_item_of_kind(client, "reactivate")["item_id"]).get_json()
    assert back["ai_system"]["retired"] is False
    assert back["ai_system"]["data"]["signoff_history"][-1]["kind"] == "reactivate"
    # Editing works again once it is back in the estate.
    assert client.post(f"{_AI}/AIS-0001/field",
                       json={"field": "use_case", "value": "Summarises client mail.",
                             "confirmed": True}, headers=HEADERS).status_code == 200


def test_rejecting_a_retire_leaves_the_ai_system_active(client):
    _ready(client, register_ai, "AIS-0001", _AI)
    request_retire(client, "AIS-0001", api=_AI)
    payload = decide(client, signoff_item_of_kind(client, "retire")["item_id"],
                     outcome="reject").get_json()
    assert payload["ai_system"]["retired"] is False
    assert payload["ai_system"]["data"]["signoff_history"][-1]["outcome"] == "Rejected"


# --- ML Application -----------------------------------------------------------


def test_requesting_retire_of_an_ml_application_does_not_hibernate_it(client):
    _ready(client, register_ml, "MLA-0001", _ML)
    assert request_retire(client, "MLA-0001", api=_ML).status_code == 201
    record = client.get(f"{_ML}/MLA-0001").get_json()
    assert record["retired"] is False
    request = record["data"]["signoff_requests"][0]
    assert request["kind"] == "retire" and request["status"] == "Attached"
    assert signoff_item_of_kind(client, "retire")["subject_ml_application_id"] == "MLA-0001"


def test_the_committee_hibernates_an_ml_application_and_can_bring_it_back(client):
    _ready(client, register_ml, "MLA-0001", _ML)
    request_retire(client, "MLA-0001", api=_ML)
    payload = decide(client, signoff_item_of_kind(client, "retire")["item_id"]).get_json()
    assert payload["ml_application"]["retired"] is True
    assert client.get(f"{_ML}").get_json() == [], "out of the estate once ratified"

    assert request_reactivate(client, "MLA-0001", api=_ML).status_code == 201
    back = decide(client, signoff_item_of_kind(client, "reactivate")["item_id"]).get_json()
    assert back["ml_application"]["retired"] is False
    assert [r["ml_application_id"] for r in client.get(_ML).get_json()] == ["MLA-0001"]


# --- The refusals, for both ---------------------------------------------------


def test_a_lifecycle_request_needs_a_covering_committee(client):
    """Routed to the committee responsible for the division. With none configured the
    request is refused rather than applied."""
    register_ai(client, division="Nowhere")
    response = request_retire(client, "AIS-0001", api=_AI)
    assert response.status_code == 400
    assert "no MRC committee covers this AI System's" in response.get_json()["error"]


def test_a_lifecycle_request_names_the_record_type_it_could_not_find(client):
    assert request_retire(client, "NOPE", api=_AI).status_code == 404
    assert request_retire(client, "NOPE", api=_ML).get_json()["error"] == \
        "ML Application not found"


def test_the_state_the_request_needs_is_checked(client):
    _ready(client, register_ai, "AIS-0001", _AI)
    # Not retired, so there is nothing to bring back.
    assert request_reactivate(client, "AIS-0001", api=_AI).status_code == 400
    request_retire(client, "AIS-0001", api=_AI)
    decide(client, signoff_item_of_kind(client, "retire")["item_id"])
    # Already hibernated, so it cannot be retired again.
    assert request_retire(client, "AIS-0001", api=_AI).status_code == 400


def test_asking_to_hibernate_is_confirm_to_amend(client):
    """The owner confirms the request and the MRC ratifies it — two gates, and this
    is the first. Unconfirmed it is refused before anything is queued."""
    _ready(client, register_ml, "MLA-0001", _ML)
    response = client.post(f"{_ML}/MLA-0001/request-retire", json={}, headers=HEADERS)
    assert response.status_code == 409
    assert client.get(f"{_ML}/MLA-0001").get_json()["data"].get("signoff_requests") in (
        None, [])


def test_there_is_no_way_to_retire_outside_the_committee(client):
    """The Danger tab used to POST here. The route is gone, not merely unlinked —
    an un-gated second path to the same event is the whole defect."""
    register_ai(client)
    register_ml(client)
    assert client.post(f"{_AI}/AIS-0001/retire", json={"confirmed": True},
                       headers=HEADERS).status_code == 404
    assert client.post(f"{_ML}/MLA-0001/retire", json={"confirmed": True},
                       headers=HEADERS).status_code == 404
