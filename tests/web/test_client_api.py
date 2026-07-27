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


def test_pack_preview_lists_planned_contents_without_building(client):
    # No stub_latex fixture: the preview must not compile any PDF.
    _register(client)
    _link_model(client)
    prev = client.get("/api/clients/CL-001/pack/preview")
    assert prev.status_code == 200
    body = prev.get_json()
    assert body["models"][0]["model_id"] == "MKM-EF-001"
    assert body["includes_gaps_audit"] is True
    # No ToR uploaded in a fresh instance -> surfaced as a warning up front.
    assert any("Terms of Reference" in w for w in body["warnings"])
    # Nothing was retained by previewing.
    assert client.get("/api/clients/CL-001").get_json()["data"].get("packs", []) == []


def test_pack_endpoints_404_for_unknown_client_or_pack(client, stub_latex):
    assert client.post("/api/clients/CL-404/pack", json={}, headers=HEADERS).status_code == 404
    assert client.get("/api/clients/CL-404/pack/preview").status_code == 404
    assert client.get("/api/clients/CL-404/packs/CLP-001.zip").status_code == 404
    _register(client)
    assert client.get("/api/clients/CL-001/packs/CLP-999.zip").status_code == 404


def test_supplementary_documents_lifecycle_and_pack_inclusion(client, stub_latex):
    import io as _io

    _register(client)
    up = client.post("/api/clients/CL-001/documents", headers=HEADERS,
                     data={"file": (_io.BytesIO(b"%PDF-extra"), "cover_note.pdf"),
                           "description": "Cover note"},
                     content_type="multipart/form-data")
    assert up.status_code == 201
    doc = up.get_json()["data"]["documents"][0]
    # It shows in the preview and, once generated, in the retained pack.
    prev = client.get("/api/clients/CL-001/pack/preview").get_json()
    assert prev["supplementary"][0]["name"] == "cover_note.pdf"
    row = client.post("/api/clients/CL-001/pack", json={}, headers=HEADERS).get_json()["data"]["packs"][0]
    dl = client.get("/api/clients/CL-001/packs/" + row["item_id"] + ".zip")
    names = zipfile.ZipFile(io.BytesIO(dl.data)).namelist()
    assert "supplementary/cover_note.pdf" in names
    # Download and delete the supplementary doc.
    got = client.get("/api/clients/CL-001/documents/" + doc["item_id"] + "/download")
    assert got.status_code == 200 and got.data == b"%PDF-extra"
    client.post("/api/clients/CL-001/documents/" + doc["item_id"] + "/delete", headers=HEADERS)
    assert client.get("/api/clients/CL-001").get_json()["data"].get("documents", []) == []


def test_document_endpoints_404_and_reject_empty(client):
    assert client.post("/api/clients/CL-404/documents", headers=HEADERS,
                       content_type="multipart/form-data").status_code == 404
    _register(client)
    assert client.post("/api/clients/CL-001/documents", headers=HEADERS,
                       content_type="multipart/form-data").status_code == 400
    assert client.get("/api/clients/CL-001/documents/DOC-999/download").status_code == 404
    assert client.post("/api/clients/CL-001/documents/DOC-999/delete",
                       headers=HEADERS).status_code == 404


def test_download_document_404_when_file_gone(client):
    import io as _io
    from src.files import upload_path
    from src.governance.documents import client_scope

    _register(client)
    doc = client.post("/api/clients/CL-001/documents", headers=HEADERS,
                      data={"file": (_io.BytesIO(b"%PDF-x"), "note.pdf")},
                      content_type="multipart/form-data").get_json()["data"]["documents"][0]
    upload_path(client_scope("CL-001"), doc["filename"]).unlink()
    assert client.get("/api/clients/CL-001/documents/" + doc["item_id"] + "/download").status_code == 404


def test_upload_rejects_disallowed_extension(client):
    import io as _io

    _register(client)
    bad = client.post("/api/clients/CL-001/documents", headers=HEADERS,
                      data={"file": (_io.BytesIO(b"x"), "malware.exe")},
                      content_type="multipart/form-data")
    assert bad.status_code == 400


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
    # The commit step compiles PDFs, so a missing engine is a clean 503. The
    # preview step does not compile, so it stays available even without tectonic.
    assert client.post("/api/clients/CL-001/pack", json={}, headers=HEADERS).status_code == 503
    assert client.get("/api/clients/CL-001/pack/preview").status_code == 200
