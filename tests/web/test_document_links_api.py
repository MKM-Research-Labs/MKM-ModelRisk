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
"""Documents filed as a link, through the same endpoint and panels as an upload."""
from __future__ import annotations

import io
import zipfile

from src.files import upload_path
from src.governance.documents import model_scope
from tests.web.conftest import HEADERS

SPEC = "https://wiki.example.com/models/alpha/spec"


def _register(client):
    client.post("/api/models", json={"model_id": "M1", "name": "Alpha", "confirmed": True},
                headers=HEADERS)


def _link(client, url=SPEC, title="Alpha spec", category="Core Documentation",
          base="/api/models/M1"):
    return client.post(base + "/documents",
                       data={"url": url, "title": title, "category": category,
                             "description": "Wiki"},
                       content_type="multipart/form-data", headers=HEADERS)


def test_a_link_is_filed_as_a_document_of_its_category(client):
    _register(client)
    response = _link(client)
    assert response.status_code == 201
    doc = response.get_json()["data"]["documents"][0]
    assert doc["url"] == SPEC
    assert doc["category"] == "Core Documentation"
    assert doc["original_name"] == "Alpha spec.url"
    assert doc["description"] == "Wiki"
    # Stored as a real shortcut file, which is what lets every pack and check that
    # walks a record's files treat it like any other document.
    stored = upload_path(model_scope("M1"), doc["filename"]).read_bytes()
    assert stored == b"[InternetShortcut]\r\nURL=" + SPEC.encode() + b"\r\n"


def test_downloading_a_link_opens_the_address(client):
    _register(client)
    doc = _link(client).get_json()["data"]["documents"][0]
    for suffix in ("", "?inline=1"):
        response = client.get("/api/models/M1/documents/" + doc["item_id"] + "/download" + suffix)
        assert response.status_code == 302
        assert response.headers["Location"] == SPEC


def test_a_tampered_address_is_served_as_the_shortcut_never_redirected(client, monkeypatch):
    _register(client)
    doc = _link(client).get_json()["data"]["documents"][0]
    bad = {**doc, "url": "javascript:alert(1)"}
    monkeypatch.setattr("src.web.api_models.find_document", lambda *a: bad)
    response = client.get("/api/models/M1/documents/" + doc["item_id"] + "/download")
    assert response.status_code == 200
    assert "attachment" in response.headers["Content-Disposition"]


def test_a_link_is_offered_for_tabling_and_carried_in_the_pack(client, monkeypatch):
    monkeypatch.setattr("src.governance.mrc.pack.compile_tex", lambda tex, assets=None: b"%PDF-")
    _register(client)
    _link(client, category="Analysis")
    tabled = client.get("/api/models/M1/reviewable-documents").get_json()
    assert [d["original_name"] for d in tabled] == ["Alpha spec.url"]
    archive = zipfile.ZipFile(io.BytesIO(client.get("/api/models/M1/pack.zip").data))
    assert archive.read("Analysis/Alpha spec.url").startswith(b"[InternetShortcut]")


def test_a_link_without_a_title_is_named_from_its_address(client):
    _register(client)
    doc = _link(client, url="https://drive.example.com/docs/Validation%20Report.pdf",
                title="").get_json()["data"]["documents"][0]
    assert doc["original_name"] == "Validation Report.pdf.url"


def test_only_web_addresses_are_accepted(client):
    _register(client)
    for bad in ("javascript:alert(1)", "file:///etc/passwd", "wiki/page",
                "https://a.example.com/x y", "https://", "https://a.example.com/" + "x" * 2100):
        response = _link(client, url=bad)
        assert response.status_code == 400, bad


def test_a_second_document_of_the_same_name_is_refused(client):
    """Two documents stored under one file name would share it on disk, so the second
    link would silently repoint the first — refused, as stored rather than as typed."""
    _register(client)
    assert _link(client, title="Spec").status_code == 201
    response = _link(client, url="https://other.example.com/", title="Spec")
    assert response.status_code == 400
    assert "already filed" in response.get_json()["error"]


def test_neither_a_file_nor_a_link_is_refused(client):
    _register(client)
    response = client.post("/api/models/M1/documents", data={"category": "Analysis"},
                           content_type="multipart/form-data", headers=HEADERS)
    assert response.status_code == 400
    assert _link(client, category="Nonsense").status_code == 400


def test_every_record_type_with_documents_takes_a_link(client):
    """Products, ML Applications and AI Systems file documents through the same
    panel and the same request helper as a model; a product stands for the rest."""
    client.post("/api/products", json={"product_id": "PRD-1", "product": "Bond",
                                       "fields": {"calculating_agent": "Murex"},
                                       "confirmed": True}, headers=HEADERS)
    response = _link(client, base="/api/products/PRD-1")
    assert response.status_code == 201
    assert response.get_json()["data"]["documents"][0]["url"] == SPEC
