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
"""Tests for the Product HTTP API."""
from __future__ import annotations

import io

from src.files import upload_path
from tests.web.conftest import HEADERS

_FIELDS = {"analytics_model": "MKM-AN-001", "market_data_model": "NSS bond curve",
           "calculating_agent": "Murex"}


def _live_model(client, model_id="MKM-AN-001"):
    client.post("/api/models", json={"model_id": model_id, "name": "Analytics", "confirmed": True},
                headers=HEADERS)


def _register(client, product_id="Product-0001", **overrides):
    fields = {**_FIELDS, **overrides}
    return client.post("/api/products", json={"product_id": product_id, "product": "Government Bond",
                                          "fields": fields, "confirmed": True}, headers=HEADERS)


def test_fields_endpoint(client):
    _live_model(client)
    client.post("/api/reference/collections/people",
                json={"fields": {"name": "Jane"}, "confirmed": True}, headers=HEADERS)
    specs = client.get("/api/products/fields").get_json()
    assert "product" in specs["register"]
    assert specs["bindings"] == ["analytics_model", "market_data_model", "calculating_agent"]
    fields = {f["key"]: f for g in specs["groups"] for f in g["fields"]}
    assert fields["analytics_model"]["type"] == "choice" and "MKM-AN-001" in fields["analytics_model"]["options"]
    assert fields["owner"]["type"] == "choice" and "Jane" in fields["owner"]["options"]
    assert fields["notes"]["type"] == "text"
    assert any(c["key"] == "limitations" for c in specs["collections"])


def test_register_get_and_list(client):
    _live_model(client)
    assert _register(client).status_code == 201
    product = client.get("/api/products/Product-0001").get_json()
    assert product["data"]["identifier"] == "MKM-AN-001.NSS bond curve.Murex"
    assert product["data"]["status"] == "Proposed"
    assert [p["product_id"] for p in client.get("/api/products").get_json()] == ["Product-0001"]


def test_register_requires_confirmation(client):
    _live_model(client)
    res = client.post("/api/products", json={"product_id": "Product-X", "product": "Bond", "fields": _FIELDS},
                      headers=HEADERS)
    assert res.status_code == 409


def test_register_analytics_must_be_live(client):
    assert _register(client, analytics_model="DOES-NOT-EXIST").status_code == 400


def test_get_unknown_is_404(client):
    assert client.get("/api/products/Product-NONE").status_code == 404


def test_edit_field_rebind_and_retire(client):
    _live_model(client)
    _register(client)
    edited = client.post("/api/products/Product-0001/field",
                         json={"field": "status", "value": "Active", "confirmed": True}, headers=HEADERS)
    assert edited.get_json()["data"]["status"] == "Active"
    rebound = client.post("/api/products/Product-0001/rebind",
                          json={"component": "calculating_agent", "value": "Calypso", "confirmed": True},
                          headers=HEADERS)
    assert rebound.get_json()["data"]["identifier"] == "MKM-AN-001.NSS bond curve.Calypso"
    retired = client.post("/api/products/Product-0001/retire", json={"confirmed": True}, headers=HEADERS)
    assert retired.get_json()["retired"] is True


def test_collections(client):
    _live_model(client)
    _register(client)
    added = client.post("/api/products/Product-0001/collections/limitations",
                        json={"fields": {"description": "Misses barrier risk", "impact": "High"},
                              "confirmed": True}, headers=HEADERS)
    assert added.status_code == 201
    item = added.get_json()["data"]["limitations"][0]["item_id"]
    updated = client.post("/api/products/Product-0001/collections/limitations/" + item,
                          json={"fields": {"impact": "Medium"}, "confirmed": True}, headers=HEADERS)
    assert updated.get_json()["data"]["limitations"][0]["impact"] == "Medium"
    removed = client.post("/api/products/Product-0001/collections/limitations/" + item + "/delete",
                          json={"confirmed": True}, headers=HEADERS)
    assert removed.get_json()["data"].get("limitations", []) == []


def test_used_by(client):
    _live_model(client)
    _register(client, product_id="Product-0001")
    used = client.get("/api/products/used-by/MKM-AN-001").get_json()
    assert [p["product_id"] for p in used] == ["Product-0001"]
    assert client.get("/api/products/used-by/OTHER").get_json() == []


def test_fields_includes_docs_remediation_and_rag(client):
    _live_model(client)
    specs = client.get("/api/products/fields").get_json()
    assert "Core Documentation" in specs["doc_categories"]
    assert any(c["key"] == "remediation_steps" for c in specs["collections"])
    rag = {f["key"]: f for g in specs["groups"] for f in g["fields"]}["rag_rating"]
    assert rag["type"] == "choice" and "Green" in rag["options"]


def test_edit_rag_and_review_date(client):
    _live_model(client)
    _register(client)
    rag = client.post("/api/products/Product-0001/field",
                      json={"field": "rag_rating", "value": "Green", "confirmed": True}, headers=HEADERS)
    assert rag.get_json()["data"]["rag_rating"] == "Green"
    bad = client.post("/api/products/Product-0001/field",
                      json={"field": "rag_rating", "value": "Purple", "confirmed": True}, headers=HEADERS)
    assert bad.status_code == 400
    dated = client.post("/api/products/Product-0001/field",
                        json={"field": "next_review_date", "value": "2026-09-30", "confirmed": True},
                        headers=HEADERS)
    assert dated.get_json()["data"]["next_review_date"] == "2026-09-30"


def test_remediation_collection(client):
    _live_model(client)
    _register(client)
    added = client.post("/api/products/Product-0001/collections/remediation_steps",
                        json={"fields": {"description": "Migrate instance", "status": "In Progress"},
                              "confirmed": True}, headers=HEADERS)
    assert added.status_code == 201
    assert added.get_json()["data"]["remediation_steps"][0]["description"] == "Migrate instance"


def _upload_doc(client, category="Core Documentation", name="dev.pdf"):
    return client.post(
        "/api/products/Product-0001/documents",
        data={"file": (io.BytesIO(b"PRODUCTDOC"), name), "category": category, "description": "spec"},
        content_type="multipart/form-data", headers=HEADERS)


def test_product_documents_upload_download_delete(client):
    _live_model(client)
    _register(client)
    up = _upload_doc(client)
    assert up.status_code == 201
    doc = up.get_json()["data"]["documents"][0]
    assert doc["category"] == "Core Documentation"
    dl = client.get("/api/products/Product-0001/documents/" + doc["item_id"] + "/download")
    assert dl.status_code == 200 and dl.data == b"PRODUCTDOC"
    rm = client.post("/api/products/Product-0001/documents/" + doc["item_id"] + "/delete",
                     json={}, headers=HEADERS)
    assert rm.get_json()["data"].get("documents", []) == []


def test_product_document_errors(client):
    _live_model(client)
    _register(client)
    assert _upload_doc(client, category="Nope").status_code == 400
    assert _upload_doc(client, name="evil.exe").status_code == 400
    no_file = client.post("/api/products/Product-0001/documents", data={"category": "Analysis"},
                          content_type="multipart/form-data", headers=HEADERS)
    assert no_file.status_code == 400
    unknown = client.post("/api/products/Product-NONE/documents", data={"category": "Analysis"},
                          content_type="multipart/form-data", headers=HEADERS)
    assert unknown.status_code == 404
    assert client.get("/api/products/Product-0001/documents/DOC-999/download").status_code == 404
    assert client.post("/api/products/Product-0001/documents/DOC-999/delete",
                       json={}, headers=HEADERS).status_code == 400


def test_product_document_missing_file_is_404(client):
    _live_model(client)
    _register(client)
    doc = _upload_doc(client).get_json()["data"]["documents"][0]
    upload_path("product/Product-0001", doc["filename"]).unlink()
    assert client.get("/api/products/Product-0001/documents/" + doc["item_id"] + "/download").status_code == 404


def _add_company(client, value="Sterling Bank plc"):
    return client.post(
        "/api/reference/collections/company",
        json={"fields": {"value": value}, "confirmed": True}, headers=HEADERS,
    )


def _register_model_with(client, model_id, **fields):
    return client.post(
        "/api/models", json={"model_id": model_id, "name": "Analytics",
                              "fields": fields, "confirmed": True}, headers=HEADERS,
    )


def test_product_rejected_when_analytics_model_has_no_company(client):
    # Simulate an orphan: the analytics model was registered first (no
    # Company existed yet), then the org admin set one up. A Product trying to
    # bind to that orphan model must now be rejected.
    _live_model(client)
    _add_company(client)
    response = _register(client)
    assert response.status_code == 400
    assert "no Company" in response.get_json()["error"]


def test_product_accepted_when_analytics_model_has_company(client):
    _add_company(client)
    _register_model_with(client, "MKM-AN-001", company="Sterling Bank plc")
    response = _register(client)
    assert response.status_code == 201
