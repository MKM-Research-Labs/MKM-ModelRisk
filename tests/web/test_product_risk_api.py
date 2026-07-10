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
                      "fields": {"analytics_model": "M1", "market_data_model": "m",
                                 "calculating_agent": "c"},
                      "confirmed": True}, headers=HEADERS)
    for field, value in fields.items():
        client.post(f"/api/products/{product_id}/field",
                    json={"field": field, "value": value, "confirmed": True}, headers=HEADERS)


def test_risk_rating_endpoint_returns_composite_and_heatmap(client):
    _model(client)
    _product(client, tier="1", materiality="High", complexity="High")
    r = client.get("/api/products/P1/risk-rating").get_json()
    assert r["rating"] in ("Acceptable", "Conditional", "Unacceptable")
    assert "components" in r and r["components"]
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


def test_validation_and_events_collections_are_available(client):
    _model(client)
    _product(client)
    specs = client.get("/api/products/fields").get_json()
    keys = {c["key"] for c in specs["collections"]}
    assert {"validation_questions", "operational_failure_events"} <= keys
    # And a validation question can be recorded on a product.
    resp = client.post("/api/products/P1/collections/validation_questions",
                       json={"fields": {"question": "Backtested?", "status": "Addressed"},
                             "confirmed": True}, headers=HEADERS)
    assert resp.status_code in (200, 201)
