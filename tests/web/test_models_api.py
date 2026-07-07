# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Tests for the model-inventory HTTP API."""
from __future__ import annotations

from tests.web.conftest import HEADERS


def _register(client, model_id="M1", name="Alpha", **fields):
    return client.post(
        "/api/models",
        json={"model_id": model_id, "name": name, "fields": fields, "confirmed": True},
        headers=HEADERS,
    )


def test_register_then_list_and_get(client):
    response = _register(client, tier=2, owner="bob")
    assert response.status_code == 201
    assert response.get_json()["data"]["name"] == "Alpha"

    listing = client.get("/api/models").get_json()
    assert [m["model_id"] for m in listing] == ["M1"]

    one = client.get("/api/models/M1").get_json()
    assert one["data"]["owner"] == "bob"
    assert one["data"]["tier"] == 2


def test_get_unknown_model_is_404(client):
    assert client.get("/api/models/none").status_code == 404


def test_register_seeds_sr262_validation_questions(client):
    _register(client)
    data = client.get("/api/models/M1").get_json()["data"]
    questions = data["validation_questions"]
    assert len(questions) == 9
    assert questions[0]["short_label"] == "Ronseal Test"
    assert all(q["status"] == "Not Addressed" for q in questions)


def test_risk_rating_endpoint(client):
    _register(client)
    rating = client.get("/api/models/M1/risk-rating").get_json()
    assert rating["rating"] in ("Acceptable", "Conditional", "Unacceptable")
    assert len(rating["components"]) == 5


def test_risk_rating_unknown_model_is_404(client):
    assert client.get("/api/models/none/risk-rating").status_code == 404


def test_risk_report_pdf(client, monkeypatch):
    monkeypatch.setattr("src.governance.mrc.pack.compile_tex", lambda tex, assets=None: b"%PDF-stub")
    _register(client)
    response = client.get("/api/models/risk-report.pdf")
    assert response.status_code == 200
    assert response.mimetype == "application/pdf"
    assert response.data.startswith(b"%PDF")


def test_field_specs_endpoint(client):
    specs = client.get("/api/models/fields").get_json()
    group_names = [g["group"] for g in specs["groups"]]
    assert "Organisation" in group_names
    org = next(g for g in specs["groups"] if g["group"] == "Organisation")
    org_keys = [f["key"] for f in org["fields"]]
    assert org_keys == ["company", "division", "department", "repo_location", "codebase"]
    # A choice field carries its options for the UI to render a dropdown.
    rag = next(f for g in specs["groups"] for f in g["fields"] if f["key"] == "rag_rating")
    assert rag["type"] == "choice"
    assert "Amber" in rag["options"]
    # Company/Division are set via the header org-scope selector, not the register form.
    assert "company" not in specs["register"]
    assert "tier" in specs["register"]


def test_type_field_is_a_choice_on_the_register_form(client):
    specs = client.get("/api/models/fields").get_json()
    model_type = next(f for g in specs["groups"] for f in g["fields"] if f["key"] == "type")
    assert model_type["type"] == "choice"
    assert list(model_type["options"]) == ["Analytical Model", "Market Data Model", "Other"]
    assert "type" in specs["register"]


def test_register_market_data_model_type(client):
    assert _register(client, model_id="STB-MD-1", type="Market Data Model").status_code == 201
    assert client.get("/api/models/STB-MD-1").get_json()["data"]["type"] == "Market Data Model"


def test_register_rejects_unknown_type(client):
    assert _register(client, model_id="M-BAD", type="Spreadsheet").status_code == 400


def test_register_with_organisation_fields(client):
    response = client.post(
        "/api/models",
        json={
            "model_id": "MKM-CR-001",
            "name": "Retail Credit Scoring",
            "fields": {
                "company": "MKM Bank",
                "division": "Risk",
                "repo_location": "git@github.com:mkm/credit.git",
                "codebase": "credit-scoring",
                "tier": 2,
                "owner": "jane@firm",
            },
            "confirmed": True,
        },
        headers=HEADERS,
    )
    assert response.status_code == 201
    data = client.get("/api/models/MKM-CR-001").get_json()["data"]
    assert data["company"] == "MKM Bank"
    assert data["division"] == "Risk"
    assert data["repo_location"] == "git@github.com:mkm/credit.git"
    assert data["codebase"] == "credit-scoring"


def test_update_field_records_actor(client):
    _register(client)
    response = client.post(
        "/api/models/M1/field",
        json={"field": "owner", "value": "carol", "confirmed": True},
        headers={"X-Auth-Request-User": "carol@corp"},
    )
    assert response.status_code == 200
    assert response.get_json()["data"]["owner"] == "carol"


def test_retire_marks_model(client):
    _register(client)
    response = client.post("/api/models/M1/retire", json={"confirmed": True}, headers=HEADERS)
    assert response.status_code == 200
    assert response.get_json()["retired"] is True


def test_mutation_without_confirmation_is_409(client):
    response = client.post(
        "/api/models",
        json={"model_id": "M1", "name": "Alpha"},  # no confirmed flag
        headers=HEADERS,
    )
    assert response.status_code == 409
    assert response.get_json()["needs_confirmation"] is True
    # Nothing was written.
    assert client.get("/api/models").get_json() == []


def test_domain_error_is_400(client):
    _register(client)
    response = _register(client)  # duplicate
    assert response.status_code == 400
    assert "already registered" in response.get_json()["error"]


def test_invalid_field_value_is_400(client):
    _register(client)
    response = client.post(
        "/api/models/M1/field",
        json={"field": "rag_rating", "value": "Purple", "confirmed": True},
        headers=HEADERS,
    )
    assert response.status_code == 400


def _schedule_meeting(client, meeting_id="MTG1"):
    return client.post(
        "/api/meetings",
        json={"meeting_id": meeting_id, "title": "Q1", "date": "2026-03-15", "confirmed": True},
        headers=HEADERS,
    )


def _add_meeting_item(client, collection, fields, meeting_id="MTG1"):
    return client.post(
        "/api/meetings/" + meeting_id + "/collections/" + collection,
        json={"fields": fields, "confirmed": True}, headers=HEADERS,
    )


def test_decisions_for_model(client):
    _register(client, model_id="M1", name="Alpha")
    _schedule_meeting(client)
    _add_meeting_item(client, "decisions", {"description": "Approve recal", "model_id": "M1"})
    _add_meeting_item(client, "decisions", {"description": "Unrelated"})  # no model_id

    response = client.get("/api/models/M1/decisions")
    assert response.status_code == 200
    decisions = response.get_json()
    assert [d["description"] for d in decisions] == ["Approve recal"]
    assert decisions[0]["meeting_id"] == "MTG1"


def test_actions_for_model(client):
    _register(client, model_id="M2", name="Beta")
    _schedule_meeting(client)
    _add_meeting_item(client, "actions", {"description": "Backtest", "model_id": "M2"})

    actions = client.get("/api/models/M2/actions").get_json()
    assert [a["description"] for a in actions] == ["Backtest"]


def test_decisions_and_actions_unknown_model_is_404(client):
    assert client.get("/api/models/NOPE/decisions").status_code == 404
    assert client.get("/api/models/NOPE/actions").status_code == 404


def _add_company(client, value="Sterling Bank plc"):
    return client.post(
        "/api/reference/collections/company",
        json={"fields": {"value": value}, "confirmed": True}, headers=HEADERS,
    )


def test_register_requires_company_when_admin_lists_have_one(client):
    """No inventory may exist outside a Company once the org is set up."""
    _add_company(client)
    response = _register(client, model_id="M-no-co")
    assert response.status_code == 400
    assert "company is required" in response.get_json()["error"].lower()


def test_register_with_company_succeeds_when_required(client):
    _add_company(client)
    response = _register(client, model_id="M-co", company="Sterling Bank plc")
    assert response.status_code == 201
    assert response.get_json()["data"]["company"] == "Sterling Bank plc"


def test_register_without_company_allowed_in_fresh_repo(client):
    """Until any Company exists, registration without one stays open."""
    response = _register(client, model_id="M-fresh")
    assert response.status_code == 201
