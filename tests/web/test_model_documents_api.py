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
