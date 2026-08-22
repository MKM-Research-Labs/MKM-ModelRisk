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
"""HTTP API for ML Applications.

The record is a use case for an off-the-shelf estimator, so the two things worth
proving here are that the form can be driven from the specs the API publishes, and
that the estimator cannot be something nobody has registered.
"""
from __future__ import annotations

from config.governance import ESTIMATOR_LIST, ML_REVIEW_QUESTIONS_COLLECTION
from src.governance.reference import add_option, ensure_default_estimators
from tests.web.conftest import HEADERS

_MINIMUM = {"name": "Retail PD scorecard", "division": "Risk", "owner": "David K Kelly",
            "estimator": "GradientBoostingClassifier",
            "use_case": "Ranks retail applicants by probability of default."}


def _register(client, ml_application_id="MLA-0001", **overrides):
    return client.post("/api/ml-applications",
                       json={"ml_application_id": ml_application_id,
                             "fields": {**_MINIMUM, **overrides}, "confirmed": True},
                       headers=HEADERS)


def test_fields_publishes_groups_register_and_collections(client):
    res = client.get("/api/ml-applications/fields").get_json()
    groups = {g["group"] for g in res["groups"]}
    assert {"Organisation", "Identity", "Estimator and method", "Classification",
            "Governance"} <= groups
    assert res["register"] == ["name", "division", "owner", "estimator", "use_case"]
    keys = {c["key"] for c in res["collections"]}
    assert ML_REVIEW_QUESTIONS_COLLECTION in keys
    assert "assumptions" in keys and "signoff_history" in keys


def test_versions_are_offered_per_estimator(client):
    """The version dropdown narrows to the chosen estimator, the same way the
    Product editor's model dropdown narrows to the chosen component type."""
    add_option(list_name=ESTIMATOR_LIST,
               fields={"value": "XGBRegressor", "source": "XGBoost",
                       "versions": "2.0.3, 2.1.0"}, actor="admin")
    add_option(list_name=ESTIMATOR_LIST,
               fields={"value": "OLS", "source": "statsmodels"}, actor="admin")

    versions = client.get("/api/ml-applications/fields").get_json()["versions_by_estimator"]
    assert versions["XGBRegressor"] == ["2.0.3", "2.1.0"]
    # Seeded rows carry no versions; the form falls back to free text rather than
    # offering an empty dropdown nobody can satisfy.
    assert versions["OLS"] == []


def test_register_returns_the_record_with_its_questionnaire(client):
    ensure_default_estimators()
    res = _register(client)
    assert res.status_code == 201
    data = res.get_json()["data"]
    assert data["name"] == "Retail PD scorecard"
    asked = data[ML_REVIEW_QUESTIONS_COLLECTION]
    assert asked[0]["short_label"] == "Use Case"
    assert len(asked) == 10


def test_an_estimator_nobody_registered_is_refused(client):
    """Strict, like a model's type: an ML Application cannot name a component the
    institution has never defined in Admin."""
    ensure_default_estimators()
    res = _register(client, ml_application_id="MLA-0002", estimator="SuperBoostinator")
    assert res.status_code == 400
    assert "estimator must be one of" in res.get_json()["error"]


def test_an_unknown_record_is_a_404(client):
    assert client.get("/api/ml-applications/MLA-9999").status_code == 404


def test_a_field_can_be_edited_through_the_api(client):
    ensure_default_estimators()
    _register(client)
    res = client.post("/api/ml-applications/MLA-0001/field",
                      json={"field": "estimator_rationale",
                            "value": "Gradient boosting, unscored alternatives.", "confirmed": True},
                      headers=HEADERS)
    assert res.status_code == 200
    assert res.get_json()["data"]["estimator_rationale"] == "Gradient boosting, unscored alternatives."


def test_collections_can_be_added_and_removed(client):
    ensure_default_estimators()
    _register(client)
    res = client.post("/api/ml-applications/MLA-0001/collections/limitations",
                      json={"fields": {"description": "Not calibrated below 500 GBP."},
                            "confirmed": True}, headers=HEADERS)
    assert res.status_code == 201
    item_id = res.get_json()["data"]["limitations"][0]["item_id"]

    res = client.post(
        f"/api/ml-applications/MLA-0001/collections/limitations/{item_id}/delete",
        json={"confirmed": True}, headers=HEADERS)
    assert res.get_json()["data"]["limitations"] == []


def test_retiring_through_the_api(client):
    ensure_default_estimators()
    _register(client)
    res = client.post("/api/ml-applications/MLA-0001/retire",
                      json={"confirmed": True}, headers=HEADERS)
    assert res.get_json()["retired"] is True
    assert not res.get_json()["data"].get("lifecycle_stage")


def test_the_list_endpoint_returns_registered_records(client):
    ensure_default_estimators()
    _register(client)
    _register(client, ml_application_id="MLA-0002", name="Fraud triage")
    listed = client.get("/api/ml-applications").get_json()
    assert [r["ml_application_id"] for r in listed] == ["MLA-0001", "MLA-0002"]
