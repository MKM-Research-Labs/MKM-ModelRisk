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
"""An ML Application's rating goes to the committee.

Before this it applied directly, which made the one class of record most likely to be
argued about the one class exempt from the committee that signs off everything else.
The proposal is routed to the committee responsible for the record's division and the
stored rating does not move until that committee approves it.
"""
from __future__ import annotations

from src.governance.ml_application import get_ml_application
from src.web._signoff_subject import ML_APPLICATION_SUBJECT, SUBJECTS
from tests.web.conftest import HEADERS

_MINIMUM = {"name": "Retail PD scorecard", "division": "Risk", "owner": "Dana",
            "estimator": "GradientBoostingClassifier", "use_case": "Ranks applicants."}


def _register(client, ml_application_id="MLA-0001", **overrides):
    return client.post("/api/ml-applications",
                       json={"ml_application_id": ml_application_id,
                             "fields": {**_MINIMUM, **overrides}, "confirmed": True},
                       headers=HEADERS)


def test_an_ml_application_is_a_subject_the_committee_knows():
    """A fourth registration, not a fourth route: the sign-off routing is written once
    against the Subject adapter and this joins it."""
    assert ML_APPLICATION_SUBJECT in SUBJECTS
    assert ML_APPLICATION_SUBJECT.kind == "ml_application"
    assert ML_APPLICATION_SUBJECT.agenda_id_field == "subject_ml_application_id"
    # Retire is carried; reactivate is not yet, so the committee is never offered a
    # decision the subject cannot carry out.
    assert ML_APPLICATION_SUBJECT.supports("retire")
    assert not ML_APPLICATION_SUBJECT.supports("reactivate")


def test_the_agenda_can_name_an_ml_application_as_its_subject():
    from config.governance import MRC_COLLECTION_SPECS

    keys = {f["key"] for f in MRC_COLLECTION_SPECS["agenda"]["fields"]}
    assert "subject_ml_application_id" in keys


def test_a_rating_proposal_without_a_committee_is_refused(client):
    """Routed to the committee responsible for the division. With none configured the
    request is refused rather than applied — a rating nobody signs off is not a rating
    that has been through governance."""
    _register(client, division="Nowhere")
    res = client.post("/api/ml-applications/MLA-0001/request-signoff",
                      json={"proposed_rag": "Amber", "confirmed": True}, headers=HEADERS)
    assert res.status_code == 400
    assert "no MRC committee covers" in res.get_json()["error"]


def test_a_proposal_needs_a_rating(client):
    _register(client)
    res = client.post("/api/ml-applications/MLA-0001/request-signoff",
                      json={"confirmed": True}, headers=HEADERS)
    assert res.status_code == 400


def test_an_unknown_record_is_a_404(client):
    res = client.post("/api/ml-applications/MLA-NOPE/request-signoff",
                      json={"proposed_rag": "Amber", "confirmed": True}, headers=HEADERS)
    assert res.status_code == 404


def test_the_stored_rating_does_not_move_when_a_proposal_is_raised(client):
    """The whole point. The record still says what the committee last approved."""
    from src.governance.reference import add_option

    add_option(list_name="division", fields={"value": "Risk"}, actor="admin")
    add_option(list_name="mrc", fields={"value": "MRC-RISK", "name": "Risk MRC",
                                        "level": "Division", "scope_value": "Risk"},
               actor="admin")
    _register(client)
    before = (get_ml_application("MLA-0001")["data"] or {}).get("rag_rating")
    res = client.post("/api/ml-applications/MLA-0001/request-signoff",
                      json={"proposed_rag": "Red", "confirmed": True}, headers=HEADERS)
    assert res.status_code == 201
    data = get_ml_application("MLA-0001")["data"] or {}
    assert data.get("rag_rating") == before
    pending = [r for r in data.get("signoff_requests") or []
               if r.get("proposed_rag") == "Red"]
    assert pending, "the proposal is queued for the committee"


def test_every_subject_the_routing_knows_is_a_subject_the_pack_knows():
    """The pack splits an agenda into the running order and the requests the committee
    is answering by looking for a subject field. A Subject registered in the routing but
    missing from that list is not merely unnamed: its decision is counted as part of the
    running order and never reaches the sign-offs table — which is what happened to ML
    Applications on the console's Approvals tabs. Asserted rather than remembered."""
    from src.governance.mrc._pack_signoffs import SUBJECT_FIELDS, subject_of

    assert {s.agenda_id_field for s in SUBJECTS} <= set(SUBJECT_FIELDS)
    assert subject_of({"subject_ml_application_id": "MLA-0001"}) == "MLA-0001"
    assert subject_of({"title": "Any Other Business"}) == ""


def _seed_division_mrc():
    from src.governance.reference import add_option

    add_option(list_name="division", fields={"value": "Risk"}, actor="admin")
    add_option(list_name="mrc", fields={"value": "MRC-RISK", "name": "Risk MRC",
                                        "level": "Division", "scope_value": "Risk",
                                        "quorum_require_chair": "No",
                                        "quorum_require_secretary": "No",
                                        "quorum_min_voting": "0"}, actor="admin")


def test_a_proposal_left_undecided_by_a_closed_meeting_can_be_raised_again(client):
    """A committee that closes without deciding a request leaves it Attached to a
    sealed meeting. Superseding it used to try to take the item off that meeting,
    which refuses — so the owner could never propose a rating again and the record was
    stuck. The closed meeting keeps what it was given; the request is withdrawn and
    re-raised for the next meeting, which is how a correction reaches a committee."""
    _seed_division_mrc()
    _register(client)
    client.post("/api/meetings", json={"meeting_id": "MTG-A", "title": "Q1",
                                       "date": "2026-06-30", "fields": {"mrc": "MRC-RISK"},
                                       "confirmed": True}, headers=HEADERS)
    first = client.post("/api/ml-applications/MLA-0001/request-signoff",
                        json={"proposed_rag": "Amber", "confirmed": True}, headers=HEADERS)
    assert first.status_code == 201
    client.post("/api/meetings/MTG-A/field",
                json={"field": "status", "value": "Completed", "confirmed": True},
                headers=HEADERS)
    client.post("/api/meetings", json={"meeting_id": "MTG-B", "title": "Q2",
                                       "date": "2026-09-30", "fields": {"mrc": "MRC-RISK"},
                                       "confirmed": True}, headers=HEADERS)

    again = client.post("/api/ml-applications/MLA-0001/request-signoff",
                        json={"proposed_rag": "Red", "confirmed": True}, headers=HEADERS)
    assert again.status_code == 201, again.get_json()

    requests = (get_ml_application("MLA-0001")["data"] or {}).get("signoff_requests") or []
    stranded = [r for r in requests if r.get("proposed_rag") == "Amber"]
    assert [r["status"] for r in stranded] == ["Withdrawn"]
    live = [r for r in requests if r.get("proposed_rag") == "Red"]
    assert [r["status"] for r in live] == ["Attached"]
    assert live[0]["meeting_id"] == "MTG-B"
    # The sealed meeting is a finished record: nothing was taken off it.
    closed = client.get("/api/meetings/MTG-A").get_json()["data"]
    assert [a for a in closed["agenda"] if a.get("subject_ml_application_id")]
