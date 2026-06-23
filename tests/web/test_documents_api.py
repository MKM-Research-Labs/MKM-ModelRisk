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
"""Tests for the governance-wide Documents API."""
from __future__ import annotations

import io

from src.files import upload_path
from tests.web.conftest import HEADERS


def _upload(client, name="report.pdf"):
    return client.post(
        "/api/documents",
        data={"file": (io.BytesIO(b"PDFDATA"), name), "description": "Q1 pack"},
        content_type="multipart/form-data", headers=HEADERS,
    )


def test_upload_list_download_delete(client):
    upload = _upload(client)
    assert upload.status_code == 201
    doc = upload.get_json()[0]
    assert doc["original_name"] == "report.pdf"
    assert len(client.get("/api/documents").get_json()) == 1

    download = client.get("/api/documents/" + doc["item_id"] + "/download")
    assert download.status_code == 200 and download.data == b"PDFDATA"

    deleted = client.post("/api/documents/" + doc["item_id"] + "/delete", headers=HEADERS)
    assert deleted.get_json() == []


def test_no_file_is_400(client):
    response = client.post("/api/documents", data={}, content_type="multipart/form-data", headers=HEADERS)
    assert response.status_code == 400


def test_bad_extension_is_400(client):
    assert _upload(client, "evil.exe").status_code == 400


def test_download_unknown_is_404(client):
    assert client.get("/api/documents/DOC-999/download").status_code == 404


def test_download_missing_file_is_404(client):
    doc = _upload(client).get_json()[0]
    upload_path("governance", doc["filename"]).unlink()
    assert client.get("/api/documents/" + doc["item_id"] + "/download").status_code == 404


def test_delete_unknown_is_400(client):
    assert client.post("/api/documents/DOC-999/delete", headers=HEADERS).status_code == 400
