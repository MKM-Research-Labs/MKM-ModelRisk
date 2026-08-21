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
