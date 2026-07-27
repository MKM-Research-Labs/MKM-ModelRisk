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
"""Tests for the Client HTTP API."""
from __future__ import annotations

import io
import zipfile

import pytest

from src.governance.mrc.pack import TectonicNotFound
from tests.web.conftest import HEADERS


@pytest.fixture
def stub_latex(monkeypatch):
    """Stub the LaTeX compiler so pack generation needs no tectonic binary."""
    monkeypatch.setattr("src.governance.mrc.pack.compile_tex",
                        lambda tex, assets=None: b"%PDF-stub")


def _register(client, name="Acme Bank", **fields):
    return client.post("/api/clients", json={"name": name, "fields": fields, "confirmed": True},
                       headers=HEADERS)


def test_fields_endpoint(client):
    client.post("/api/reference/collections/people",
                json={"fields": {"name": "Jane"}, "confirmed": True}, headers=HEADERS)
    specs = client.get("/api/clients/fields").get_json()
    assert specs["register"] == ["name"]
    keys = {c["key"] for c in specs["collections"]}
    assert {"divisions", "departments", "contacts", "links"} <= keys
    fields = {f["key"]: f for g in specs["groups"] for f in g["fields"]}
    # relationship_owner resolves to a people dropdown once the list is populated.
    assert fields["relationship_owner"]["type"] == "choice"
    assert "Jane" in fields["relationship_owner"]["options"]


def test_register_get_and_list(client):
    assert _register(client).status_code == 201
    assert _register(client, name="Globex").status_code == 201
    acme = client.get("/api/clients/CL-001").get_json()
    assert acme["data"]["name"] == "Acme Bank" and acme["data"]["status"] == "Active"
    assert [c["client_id"] for c in client.get("/api/clients").get_json()] == ["CL-001", "CL-002"]


def test_register_requires_confirmation(client):
    res = client.post("/api/clients", json={"name": "Acme Bank"}, headers=HEADERS)
    assert res.status_code == 409 and res.get_json()["needs_confirmation"]


def test_get_unknown_is_404(client):
    assert client.get("/api/clients/CL-404").status_code == 404


def test_org_tree_contacts_and_edit(client):
    _register(client)
    client.post("/api/clients/CL-001/field",
                json={"field": "sector", "value": "Banking", "confirmed": True}, headers=HEADERS)
    client.post("/api/clients/CL-001/collections/divisions",
                json={"fields": {"value": "Risk"}, "confirmed": True}, headers=HEADERS)
    client.post("/api/clients/CL-001/collections/departments",
                json={"fields": {"value": "Model Validation", "division": "Risk"},
                      "confirmed": True}, headers=HEADERS)
    res = client.post("/api/clients/CL-001/collections/contacts",
                      json={"fields": {"name": "Dana Lee", "email": "dana@acme.test",
                                       "role": "Head of MV", "department": "Model Validation"},
                            "confirmed": True}, headers=HEADERS)
    assert res.status_code == 201
    data = client.get("/api/clients/CL-001").get_json()["data"]
    assert data["sector"] == "Banking"
    assert data["divisions"][0]["value"] == "Risk"
    assert data["contacts"][0]["name"] == "Dana Lee"


def test_link_lifecycle(client):
    _register(client)
    client.post("/api/clients/CL-001/collections/links",
                json={"fields": {"link_type": "Model", "subject_id": "MKM-EF-001"},
                      "confirmed": True}, headers=HEADERS)
    client.post("/api/clients/CL-001/collections/links/CLL-001",
                json={"fields": {"note": "primary"}, "confirmed": True}, headers=HEADERS)
    link = client.get("/api/clients/CL-001").get_json()["data"]["links"][0]
    assert link["subject_id"] == "MKM-EF-001" and link["note"] == "primary"
    client.post("/api/clients/CL-001/collections/links/CLL-001/delete",
                json={"confirmed": True}, headers=HEADERS)
    assert client.get("/api/clients/CL-001").get_json()["data"].get("links", []) == []


def test_link_options(client):
    _register(client)
    client.post("/api/models", json={"model_id": "MKM-EF-001", "name": "Event Frequency",
                                      "confirmed": True}, headers=HEADERS)
    client.post("/api/products", json={"product_id": "Product-0001", "product": "Bond",
                                        "fields": {"calculating_agent": "Murex"},
                                        "confirmed": True}, headers=HEADERS)
    opts = client.get("/api/clients/CL-001/link-options").get_json()
    assert {"id": "MKM-EF-001", "label": "Event Frequency"} in opts["models"]
    assert {"id": "Product-0001", "label": "Bond"} in opts["products"]


def test_retire_makes_read_only(client):
    _register(client)
    res = client.post("/api/clients/CL-001/retire", json={"confirmed": True}, headers=HEADERS)
    assert res.status_code == 200 and res.get_json()["retired"]
    bad = client.post("/api/clients/CL-001/field",
                      json={"field": "notes", "value": "x", "confirmed": True}, headers=HEADERS)
    assert bad.status_code == 400


def _link_model(client):
    client.post("/api/models", json={"model_id": "MKM-EF-001", "name": "Event Frequency",
                                      "confirmed": True}, headers=HEADERS)
    client.post("/api/clients/CL-001/collections/links",
                json={"fields": {"link_type": "Model", "subject_id": "MKM-EF-001"},
                      "confirmed": True}, headers=HEADERS)


def test_generate_pack_retains_a_bitemporal_history_row(client, stub_latex):
    _register(client)
    _link_model(client)
    res = client.post("/api/clients/CL-001/pack", json={}, headers=HEADERS)
    assert res.status_code == 201
    packs = res.get_json()["data"]["packs"]
    assert len(packs) == 1
    row = packs[0]
    assert row["as_of"] and row["generated_at"] and row["filename"].endswith(".zip")
    assert int(row["size"]) > 0
    # The retained ZIP downloads and is a real archive holding the linked model doc.
    dl = client.get("/api/clients/CL-001/packs/" + row["item_id"] + ".zip")
    assert dl.status_code == 200 and dl.mimetype == "application/zip"
    names = zipfile.ZipFile(io.BytesIO(dl.data)).namelist()
    assert "models/MKM-EF-001/MKM-EF-001_model_risk_document.pdf" in names
    assert "governance/completeness_audit.pdf" in names


def test_pack_zip_on_demand_is_not_retained(client, stub_latex):
    _register(client)
    res = client.get("/api/clients/CL-001/pack.zip")
    assert res.status_code == 200 and res.mimetype == "application/zip"
    assert client.get("/api/clients/CL-001").get_json()["data"].get("packs", []) == []


def test_pack_endpoints_404_for_unknown_client_or_pack(client, stub_latex):
    assert client.post("/api/clients/CL-404/pack", json={}, headers=HEADERS).status_code == 404
    assert client.get("/api/clients/CL-404/pack.zip").status_code == 404
    assert client.get("/api/clients/CL-404/packs/CLP-001.zip").status_code == 404
    _register(client)
    assert client.get("/api/clients/CL-001/packs/CLP-999.zip").status_code == 404


def test_download_pack_404_when_the_retained_file_is_gone(client, stub_latex):
    from src.files import upload_path

    _register(client)
    row = client.post("/api/clients/CL-001/pack", json={}, headers=HEADERS).get_json()["data"]["packs"][0]
    upload_path("client_pack/CL-001", row["filename"]).unlink()
    assert client.get("/api/clients/CL-001/packs/" + row["item_id"] + ".zip").status_code == 404


def test_pack_returns_503_when_tectonic_missing(client, monkeypatch):
    def _boom(tex, assets=None):
        raise TectonicNotFound("no tectonic")
    monkeypatch.setattr("src.governance.mrc.pack.compile_tex", _boom)
    _register(client)
    assert client.post("/api/clients/CL-001/pack", json={}, headers=HEADERS).status_code == 503
    assert client.get("/api/clients/CL-001/pack.zip").status_code == 503
