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
"""Tests for the Product HTTP API."""
from __future__ import annotations

import io

from config.governance import DEFAULT_RACI
from src.files import upload_path
from tests.web.conftest import HEADERS

_FIELDS = {"calculating_agent": "Murex"}


def _live_model(client, model_id="MKM-AN-001"):
    client.post("/api/models", json={"model_id": model_id, "name": "Analytics", "confirmed": True},
                headers=HEADERS)


def _component(client, product_id="Product-0001", model_id="MKM-AN-001",
               component_type="Analytical Model"):
    """Bind a model to a Product as a component, as the detail view does."""
    return client.post(f"/api/products/{product_id}/collections/components",
                       json={"fields": {"component_type": component_type,
                                        "model_id": model_id},
                             "confirmed": True}, headers=HEADERS)


def _register(client, product_id="Product-0001", **overrides):
    fields = {**_FIELDS, **overrides}
    return client.post("/api/products", json={"product_id": product_id, "product": "Government Bond",
                                          "fields": fields, "confirmed": True}, headers=HEADERS)


def test_fields_endpoint(client):
    _live_model(client)
    client.post("/api/reference/collections/people",
                json={"fields": {"name": "Jane"}, "confirmed": True}, headers=HEADERS)
    client.post("/api/reference/collections/division",
                json={"fields": {"value": "Markets"}, "confirmed": True}, headers=HEADERS)
    specs = client.get("/api/products/fields").get_json()
    assert "product" in specs["register"]
    assert specs["bindings"] == ["calculating_agent"]
    # Components are a collection now, and the endpoint says which live models can
    # fill each type so the editor can narrow its dropdown.
    assert specs["components"] == "components"
    assert "MKM-AN-001" in [m for ids in specs["models_by_type"].values() for m in ids]
    assert any(c["key"] == "components" for c in specs["collections"])
    fields = {f["key"]: f for g in specs["groups"] for f in g["fields"]}
    assert fields["owner"]["type"] == "choice" and "Jane" in fields["owner"]["options"]
    # Org fields resolve to reference-backed dropdowns once the list is populated,
    # exactly like a model's (line_of_business stays text here — none seeded yet).
    assert fields["division"]["type"] == "choice" and "Markets" in fields["division"]["options"]
    assert "line_of_business" in fields
    assert fields["notes"]["type"] == "text"
    assert any(c["key"] == "limitations" for c in specs["collections"])


def test_register_get_and_list(client):
    _live_model(client)
    assert _register(client).status_code == 201
    product = client.get("/api/products/Product-0001").get_json()
    # Nothing bound yet, so there is no identity to derive.
    assert product["data"]["identifier"] is None
    _component(client)
    product = client.get("/api/products/Product-0001").get_json()
    assert product["data"]["identifier"] == "MKM-AN-001.Murex"
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


def test_edit_field_and_rebind(client):
    _live_model(client)
    _register(client)
    _component(client)
    edited = client.post("/api/products/Product-0001/field",
                         json={"field": "status", "value": "Active", "confirmed": True}, headers=HEADERS)
    assert edited.get_json()["data"]["status"] == "Active"
    rebound = client.post("/api/products/Product-0001/rebind",
                          json={"component": "calculating_agent", "value": "Calypso", "confirmed": True},
                          headers=HEADERS)
    assert rebound.get_json()["data"]["identifier"] == "MKM-AN-001.Calypso"


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
    _component(client)
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


# The Product ↔ analytics-model company check retired with Phase MRC-5: the
# instance is a single institution, so every model belongs to it by default.


def test_raci_roles_collection_on_a_product(client):
    # RACI folds into Product: the operating-model roles are defined at product level.
    _live_model(client)
    _register(client)
    resp = client.post(
        "/api/products/Product-0001/collections/raci_roles",
        json={"fields": {"role": "Operations Lead", "raci": "Responsible",
                         "description": "Reruns failed production jobs"}, "confirmed": True},
        headers=HEADERS,
    )
    assert resp.status_code == 201
    # Registration scaffolds the four DEFAULT_RACI accountabilities, so an added
    # role lands after them — find it by name rather than assuming it is first.
    roles = resp.get_json()["data"]["raci_roles"]
    assert len(roles) == len(DEFAULT_RACI) + 1
    role = next(r for r in roles if r["role"] == "Operations Lead")
    assert role["raci"] == "Responsible"


def test_raci_role_rejects_an_invalid_raci_code(client):
    _live_model(client)
    _register(client)
    resp = client.post(
        "/api/products/Product-0001/collections/raci_roles",
        json={"fields": {"role": "X", "raci": "Bystander"}, "confirmed": True},
        headers=HEADERS,
    )
    assert resp.status_code == 400


def test_the_model_map_names_the_components_and_annotates_the_arrows(client):
    """The map is what a reader opens to ask which models the product is actually
    made of, so the arrows carry what crosses them rather than being bare edges."""
    _live_model(client)
    _register(client)
    _component(client)
    body = client.get("/api/products/Product-0001/model-map").get_json()
    assert [n["model_id"] for n in body["nodes"]] == ["MKM-AN-001"]
    assert all("handoff" in link for link in body["links"])


def test_a_model_map_for_a_product_nobody_registered_is_404(client):
    assert client.get("/api/products/NONE/model-map").status_code == 404
