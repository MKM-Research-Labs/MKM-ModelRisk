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
"""Product risk assessment: composite rating + heatmap + MRC linkage reads,
the same engine and shape as a model's."""
from __future__ import annotations

from tests.web.conftest import HEADERS


def _model(client, model_id="M1"):
    client.post("/api/models", json={"model_id": model_id, "name": "Analytics",
                                     "confirmed": True}, headers=HEADERS)


def _product(client, product_id="P1", **fields):
    client.post("/api/products",
                json={"product_id": product_id, "product": "Bond",
                      "fields": {"calculating_agent": "c"},
                      "confirmed": True}, headers=HEADERS)
    for field, value in fields.items():
        client.post(f"/api/products/{product_id}/field",
                    json={"field": field, "value": value, "confirmed": True}, headers=HEADERS)


def test_risk_rating_endpoint_returns_the_heatmap(client):
    _model(client)
    _product(client, tier="1", materiality="High", complexity="High")
    r = client.get("/api/products/P1/risk-rating").get_json()
    assert "rating" not in r and "components" not in r
    # Heatmap RAG comes from tier band × materiality × complexity, like a model.
    assert r["heatmap"]["tier"] == "1"
    assert r["heatmap"]["rag"] is not None
    assert r["signed_off"] is False   # never signed off yet
    assert "pending_signoff" in r


def test_risk_rating_heatmap_blank_without_classification(client):
    _model(client)
    _product(client)   # no tier/materiality/complexity set
    r = client.get("/api/products/P1/risk-rating").get_json()
    assert r["heatmap"]["rag"] is None


def test_risk_rating_unknown_product_is_404(client):
    assert client.get("/api/products/none/risk-rating").status_code == 404


def test_decisions_and_actions_endpoints_empty_by_default(client):
    _model(client)
    _product(client)
    assert client.get("/api/products/P1/decisions").get_json() == []
    assert client.get("/api/products/P1/actions").get_json() == []
    assert client.get("/api/products/none/decisions").status_code == 404


def test_the_event_log_is_on_a_product_but_validation_questions_are_not(client):
    """A Product validates through its component models, so the SR 26-2
    questionnaire stays model-level; the operational-event log is product-level
    because the impact of a failure lands on the product."""
    _model(client)
    _product(client)
    specs = client.get("/api/products/fields").get_json()
    keys = {c["key"] for c in specs["collections"]}
    assert "operational_failure_events" in keys
    assert "validation_questions" not in keys
    # And the omission is enforced, not merely undisplayed.
    resp = client.post("/api/products/P1/collections/validation_questions",
                       json={"fields": {"question": "Backtested?", "status": "Addressed"},
                             "confirmed": True}, headers=HEADERS)
    assert resp.status_code == 400
    # An operational failure event, however, is recorded on the product.
    resp = client.post("/api/products/P1/collections/operational_failure_events",
                       json={"fields": {"date": "2026-08-11",
                                        "description": "Overnight job failed"},
                             "confirmed": True}, headers=HEADERS)
    assert resp.status_code in (200, 201)
