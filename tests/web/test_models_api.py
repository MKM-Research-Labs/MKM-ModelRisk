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
"""Tests for the model-inventory HTTP API."""
from __future__ import annotations

from tests.web.conftest import HEADERS


def _register(client, model_id="M1", name="Alpha", **fields):
    return client.post(
        "/api/models",
        json={"model_id": model_id, "name": name, "fields": fields, "confirmed": True},
        headers=HEADERS,
    )


def _declare_dep(client, model_id, direction, related):
    return client.post(
        f"/api/models/{model_id}/collections/dependencies",
        json={"fields": {"direction": direction, "model_id": related}, "confirmed": True},
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


def test_chain_derives_the_string_of_pearls_from_declared_dependencies(client):
    _register(client, model_id="A", name="Storm")
    _register(client, model_id="B", name="Pricer")
    assert _declare_dep(client, "A", "downstream", "B").status_code == 201
    chain = client.get("/api/models/chain").get_json()
    assert {n["model_id"] for n in chain["nodes"]} == {"A", "B"}
    assert chain["links"] == [{"from": "A", "to": "B"}]


def test_chain_refuses_a_dependency_that_would_form_a_cycle(client):
    _register(client, model_id="A", name="Storm")
    _register(client, model_id="B", name="Pricer")
    _declare_dep(client, "A", "downstream", "B")  # A -> B
    cycle = _declare_dep(client, "B", "downstream", "A")  # B -> A closes the loop
    assert cycle.status_code == 400
    assert "cycle" in cycle.get_json()["error"]


def test_register_seeds_sr262_validation_questions(client):
    _register(client)
    data = client.get("/api/models/M1").get_json()["data"]
    questions = data["validation_questions"]
    assert len(questions) == 9
    assert questions[0]["short_label"] == "Ronseal Test"
    assert all(q["status"] == "Not Addressed" for q in questions)


def test_risk_rating_endpoint(client):
    """The endpoint returns the heatmap placement and sign-off state — the
    rating the committee governs, with no second derived score beside it."""
    _register(client)
    rating = client.get("/api/models/M1/risk-rating").get_json()
    assert "heatmap" in rating and "signed_off" in rating
    assert rating["events_in_window"] == 0
    assert "rating" not in rating and "components" not in rating


def test_risk_rating_unknown_model_is_404(client):
    assert client.get("/api/models/none/risk-rating").status_code == 404


def test_risk_report_pdf(client, monkeypatch):
    monkeypatch.setattr("src.governance.mrc.pack.compile_tex", lambda tex, assets=None: b"%PDF-stub")
    _register(client)
    response = client.get("/api/models/risk-report.pdf")
    assert response.status_code == 200
    assert response.mimetype == "application/pdf"
    assert response.data.startswith(b"%PDF")


def test_model_risk_document_pdf(client, monkeypatch):
    """One model's client-facing document, generated from the inventory on request."""
    monkeypatch.setattr("src.governance.mrc.pack.compile_tex", lambda tex, assets=None: b"%PDF-stub")
    _register(client)
    response = client.get("/api/models/M1/risk-document.pdf")
    assert response.status_code == 200
    assert response.mimetype == "application/pdf"
    assert "M1_model_risk_document.pdf" in response.headers["Content-Disposition"]


def test_model_risk_document_unknown_model_is_404(client):
    assert client.get("/api/models/none/risk-document.pdf").status_code == 404


def test_model_client_pack_zip(client, monkeypatch):
    """The pack downloads as an attachment: it is a file to send on, not to read."""
    monkeypatch.setattr("src.governance.mrc.pack.compile_tex", lambda tex, assets=None: b"%PDF-stub")
    _register(client)
    response = client.get("/api/models/M1/pack.zip")
    assert response.status_code == 200
    assert response.mimetype == "application/zip"
    assert "attachment" in response.headers["Content-Disposition"]
    assert "M1_model_risk_pack.zip" in response.headers["Content-Disposition"]


def test_model_client_pack_unknown_model_is_404(client):
    assert client.get("/api/models/none/pack.zip").status_code == 404


def test_field_specs_endpoint(client):
    specs = client.get("/api/models/fields").get_json()
    group_names = [g["group"] for g in specs["groups"]]
    assert "Organisation" in group_names
    org = next(g for g in specs["groups"] if g["group"] == "Organisation")
    org_keys = [f["key"] for f in org["fields"]]
    # Phase MRC-5: Company retired — the instance is a single institution.
    assert org_keys == ["division", "line_of_business", "repo_location", "codebase"]
    # A choice field carries its options for the UI to render a dropdown.
    rag = next(f for g in specs["groups"] for f in g["fields"] if f["key"] == "rag_rating")
    assert rag["type"] == "choice"
    assert "Amber" in rag["options"]
    assert "company" not in specs["register"]
    assert "tier" in specs["register"]


def test_type_field_is_a_choice_on_the_register_form(client, seeded_model_types):
    specs = client.get("/api/models/fields").get_json()
    model_type = next(f for g in specs["groups"] for f in g["fields"] if f["key"] == "type")
    assert model_type["type"] == "choice"
    # The values come from the admin model_type list, not a hardcoded vocabulary.
    assert list(model_type["options"]) == [
        "Analytical Model", "Curve Model", "Market Data Model", "Other"]
    assert "type" in specs["register"]


def test_register_market_data_model_type(client, seeded_model_types):
    assert _register(client, model_id="STB-MD-1", type="Market Data Model").status_code == 201
    assert client.get("/api/models/STB-MD-1").get_json()["data"]["type"] == "Market Data Model"


def test_register_rejects_unknown_type(client, seeded_model_types):
    assert _register(client, model_id="M-BAD", type="Spreadsheet").status_code == 400


def test_register_with_organisation_fields(client):
    response = client.post(
        "/api/models",
        json={
            "model_id": "MKM-CR-001",
            "name": "Retail Credit Scoring",
            "fields": {
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


def test_there_is_no_route_that_retires_a_model_outright(client):
    """Hibernating a model takes MRC ratification. The owner raises a request
    (POST /request-retire) and only an approval appends ModelRetired — there is
    deliberately no route that retires it directly. The full journey is covered
    in test_mrc_retire_api.py."""
    _register(client)
    response = client.post("/api/models/M1/retire", json={"confirmed": True}, headers=HEADERS)
    assert response.status_code == 404
    assert client.get("/api/models/M1").get_json()["retired"] is False


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


# The require-company gate has been retired (Phase MRC-5): the instance is
# always a single institution; company is no longer a per-model field.


def test_register_still_open_without_org_fields(client):
    """A model with no org fields set is still valid (division / line of business optional)."""
    response = _register(client, model_id="M-no-org")
    assert response.status_code == 201
