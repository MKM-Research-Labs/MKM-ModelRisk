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
"""Documents for an ML Application: the uploaded evidence and the generated dossier.

The ML twin of the model and product document endpoints, and it has to behave the
same way in the one respect that matters bi-temporally: the ML Application Document
is generated from the record on request, and every issued copy is filed back under
History so a reader can see what the record said on the day the document went out.
"""
from __future__ import annotations

import io

from src.files import upload_path
from src.governance.mrc.pack import TectonicNotFound
from tests.web.conftest import HEADERS

_MINIMUM = {"name": "Retail PD scorecard", "division": "Risk", "owner": "David K Kelly",
            "estimator": "GradientBoostingClassifier",
            "use_case": "Ranks retail applicants by probability of default."}


def _register(client):
    return client.post("/api/ml-applications",
                       json={"ml_application_id": "MLA-1", "fields": _MINIMUM,
                             "confirmed": True}, headers=HEADERS)


def _upload(client, name="evidence.pdf", category="Test Results"):
    return client.post(
        "/api/ml-applications/MLA-1/documents",
        data={"file": (io.BytesIO(b"PDFDATA"), name), "category": category,
              "description": "Q1"},
        content_type="multipart/form-data", headers=HEADERS)


def _stub_compile(monkeypatch):
    monkeypatch.setattr("src.governance.mrc.pack.compile_tex",
                        lambda tex, assets=None: b"%PDF-stub")


# --- Uploaded evidence --------------------------------------------------------

def test_upload_download_and_delete(client):
    _register(client)
    upload = _upload(client)
    assert upload.status_code == 201
    doc = upload.get_json()["data"]["documents"][0]
    assert doc["category"] == "Test Results"

    download = client.get(
        "/api/ml-applications/MLA-1/documents/" + doc["item_id"] + "/download")
    assert download.status_code == 200 and download.data == b"PDFDATA"

    deleted = client.post(
        "/api/ml-applications/MLA-1/documents/" + doc["item_id"] + "/delete",
        headers=HEADERS)
    assert deleted.get_json()["data"].get("documents", []) == []


def test_download_serves_a_pdf_inline_only_when_asked(client):
    _register(client)
    doc = _upload(client).get_json()["data"]["documents"][0]
    url = "/api/ml-applications/MLA-1/documents/" + doc["item_id"] + "/download"
    assert "attachment" in client.get(url).headers["Content-Disposition"]
    assert "inline" in client.get(url + "?inline=1").headers["Content-Disposition"]


def test_upload_against_a_record_nobody_registered_is_404(client):
    response = client.post(
        "/api/ml-applications/NONE/documents",
        data={"file": (io.BytesIO(b"x"), "a.pdf"), "category": "Analysis"},
        content_type="multipart/form-data", headers=HEADERS)
    assert response.status_code == 404


def test_a_category_the_institution_does_not_file_under_is_400(client):
    _register(client)
    assert _upload(client, category="Nope").status_code == 400


def test_upload_with_no_file_is_400(client):
    _register(client)
    response = client.post(
        "/api/ml-applications/MLA-1/documents", data={"category": "Analysis"},
        content_type="multipart/form-data", headers=HEADERS)
    assert response.status_code == 400


def test_an_extension_the_platform_will_not_store_is_400(client):
    _register(client)
    assert _upload(client, name="evil.exe").status_code == 400


def test_downloading_a_document_nobody_attached_is_404(client):
    _register(client)
    assert client.get(
        "/api/ml-applications/MLA-1/documents/DOC-999/download").status_code == 404


def test_a_document_whose_file_has_gone_missing_is_404_not_a_500(client):
    """The record still lists it; the file underneath is gone. That is a 404 about
    the file rather than a stack trace about the store."""
    _register(client)
    doc = _upload(client).get_json()["data"]["documents"][0]
    upload_path("ml_application/MLA-1", doc["filename"]).unlink()
    assert client.get(
        "/api/ml-applications/MLA-1/documents/" + doc["item_id"]
        + "/download").status_code == 404


# --- The generated ML Application Document ------------------------------------

def test_issuing_the_document_files_a_timestamped_copy_under_history(
        client, monkeypatch):
    """Each issue is kept rather than regenerated and lost: the copy records what
    the record looked like when the document went out."""
    _stub_compile(monkeypatch)
    _register(client)
    assert client.get("/api/ml-applications/MLA-1/document.pdf").status_code == 200
    client.get("/api/ml-applications/MLA-1/document.pdf")       # a second issue
    docs = client.get("/api/ml-applications/MLA-1").get_json()["data"]["documents"]
    history = [d for d in docs if d.get("category") == "History"]
    assert len(history) == 2, "each issue is filed under History, not overwritten"
    assert all(d["original_name"].startswith("MLA-1_ml_application_document_")
               for d in history)
    assert len({d["original_name"] for d in history}) == 2, "timestamps tell them apart"


def test_the_document_is_served_inline_and_named_for_the_record(client, monkeypatch):
    _stub_compile(monkeypatch)
    _register(client)
    response = client.get("/api/ml-applications/MLA-1/document.pdf")
    assert response.mimetype == "application/pdf"
    assert response.headers["Content-Disposition"] == \
        'inline; filename="MLA-1_ml_application_document.pdf"'


def test_a_document_for_a_record_nobody_registered_is_404(client):
    assert client.get("/api/ml-applications/NONE/document.pdf").status_code == 404


def test_a_missing_latex_toolchain_is_a_clean_503(client, monkeypatch):
    _register(client)

    def _boom(tex, assets=None):
        raise TectonicNotFound("tectonic is not installed")
    monkeypatch.setattr("src.governance.mrc.pack.compile_tex", _boom)
    response = client.get("/api/ml-applications/MLA-1/document.pdf")
    assert response.status_code == 503
    assert "tectonic" in response.get_json()["error"]
