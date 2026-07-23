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
"""Tests for the per-model document upload/download/delete API."""
from __future__ import annotations

import io

from src.files import upload_path
from tests.web.conftest import HEADERS


def _register(client):
    client.post("/api/models", json={"model_id": "M1", "name": "Alpha", "confirmed": True}, headers=HEADERS)


def _upload(client, name="report.pdf", category="Test Results"):
    return client.post(
        "/api/models/M1/documents",
        data={"file": (io.BytesIO(b"PDFDATA"), name), "category": category, "description": "Q1"},
        content_type="multipart/form-data", headers=HEADERS,
    )


def test_fields_endpoint_lists_doc_categories(client):
    cats = client.get("/api/models/fields").get_json()["doc_categories"]
    assert "Core Documentation" in cats and "Monitoring" in cats


def test_fields_endpoint_surfaces_each_category_in_one_place(client):
    """Every category belongs to exactly one panel, so the console never lists the
    same document twice. Testing evidence belongs to the Testing tab, not Docs."""
    specs = client.get("/api/models/fields").get_json()
    assert specs["doc_tab_categories"] == [
        "Core Documentation", "Sensitivity", "Analysis", "Monitoring", "History"]
    assert "Test Results" in specs["testing_doc_categories"]
    for testing_cat in specs["testing_doc_categories"]:
        assert testing_cat not in specs["doc_tab_categories"]
    assert specs["hidden_doc_extensions"] == ["tex"]


def test_download_serves_pdf_inline_only_when_asked(client):
    _register(client)
    doc = _upload(client).get_json()["data"]["documents"][0]
    url = "/api/models/M1/documents/" + doc["item_id"] + "/download"
    assert "attachment" in client.get(url).headers["Content-Disposition"]
    assert "inline" in client.get(url + "?inline=1").headers["Content-Disposition"]


def test_download_never_serves_an_unlisted_format_inline(client):
    """A .tex stays retrievable so it can be replaced, but is never rendered in this
    origin: inline display of an uploaded file runs as the application."""
    _register(client)
    doc = _upload(client, name="source.tex").get_json()["data"]["documents"][0]
    response = client.get("/api/models/M1/documents/" + doc["item_id"] + "/download?inline=1")
    assert response.status_code == 200
    assert "attachment" in response.headers["Content-Disposition"]


def test_upload_download_delete(client):
    _register(client)
    upload = _upload(client)
    assert upload.status_code == 201
    doc = upload.get_json()["data"]["documents"][0]
    assert doc["category"] == "Test Results"

    download = client.get("/api/models/M1/documents/" + doc["item_id"] + "/download")
    assert download.status_code == 200 and download.data == b"PDFDATA"

    deleted = client.post("/api/models/M1/documents/" + doc["item_id"] + "/delete", headers=HEADERS)
    assert deleted.get_json()["data"].get("documents", []) == []


def test_upload_invalid_category_is_400(client):
    _register(client)
    assert _upload(client, category="Nope").status_code == 400


def test_upload_no_file_is_400(client):
    _register(client)
    response = client.post(
        "/api/models/M1/documents", data={"category": "Analysis"},
        content_type="multipart/form-data", headers=HEADERS,
    )
    assert response.status_code == 400


def test_upload_bad_extension_is_400(client):
    _register(client)
    assert _upload(client, name="evil.exe").status_code == 400


def test_upload_unknown_model_is_404(client):
    response = client.post(
        "/api/models/none/documents",
        data={"file": (io.BytesIO(b"x"), "a.pdf"), "category": "Analysis"},
        content_type="multipart/form-data", headers=HEADERS,
    )
    assert response.status_code == 404


def test_download_unknown_document_is_404(client):
    _register(client)
    assert client.get("/api/models/M1/documents/DOC-999/download").status_code == 404


def test_download_missing_file_is_404(client):
    _register(client)
    doc = _upload(client).get_json()["data"]["documents"][0]
    upload_path("model/M1", doc["filename"]).unlink()
    assert client.get("/api/models/M1/documents/" + doc["item_id"] + "/download").status_code == 404


def test_delete_unknown_document_is_400(client):
    _register(client)
    assert client.post("/api/models/M1/documents/DOC-999/delete", headers=HEADERS).status_code == 400


def test_issuing_a_model_risk_document_files_a_timestamped_copy(client, monkeypatch):
    """Bi-temporal: the document renders the inventory as it stood when it was
    issued, so each issue is kept under History rather than regenerated and lost."""
    monkeypatch.setattr("src.governance.mrc.pack.compile_tex", lambda tex, assets=None: b"%PDF-stub")
    _register(client)
    assert client.get("/api/models/M1/risk-document.pdf").status_code == 200
    client.get("/api/models/M1/risk-document.pdf")
    docs = client.get("/api/models/M1").get_json()["data"]["documents"]
    history = [d for d in docs if d.get("category") == "History"]
    assert len(history) == 2, "each issue is filed, not overwritten"
    assert all(d["original_name"].startswith("M1_model_risk_document_") for d in history)
    assert len({d["original_name"] for d in history}) == 2, "timestamps distinguish them"


def test_reviewable_documents_offers_only_what_a_committee_reads(client):
    """The MRC tables a paper the model already holds. Core Documentation is not
    offered (it is not the analysis under review) and a .tex source is not either
    — it is the same paper in a form no committee reads."""
    _register(client)
    _upload(client, name="sens.pdf", category="Sensitivity")
    _upload(client, name="sens.tex", category="Sensitivity")
    _upload(client, name="core.pdf", category="Core Documentation")
    offered = client.get("/api/models/M1/reviewable-documents").get_json()
    names = [d["original_name"] for d in offered]
    assert "sens.pdf" in names
    assert "sens.tex" not in names
    assert "core.pdf" not in names


def test_reviewable_documents_unknown_model_is_404(client):
    assert client.get("/api/models/none/reviewable-documents").status_code == 404
