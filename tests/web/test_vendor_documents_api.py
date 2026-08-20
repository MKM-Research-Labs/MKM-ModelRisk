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
"""Tests for the Vendors panel of the Documents tab (vendor documents API)."""
from __future__ import annotations

import io

from src.files import upload_path
from src.governance.reference import add_option
from tests.web.conftest import HEADERS


def _vendor(name="Acme Analytics"):
    """Define a vendor in Admin and return its reference id."""
    add_option(list_name="vendor", fields={"value": name}, actor="admin")
    return name


def _vendor_id(client, name):
    vendors = client.get("/api/vendor-documents").get_json()["vendors"]
    return next(v["vendor_id"] for v in vendors if v["name"] == name)


def _upload(client, vendor_id, filename="contract.pdf", description="Master agreement"):
    return client.post(
        "/api/vendor-documents/" + vendor_id,
        data={"file": (io.BytesIO(b"PDFDATA"), filename), "description": description},
        content_type="multipart/form-data", headers=HEADERS,
    )


def test_vendors_come_from_the_admin_list(client):
    assert client.get("/api/vendor-documents").get_json()["vendors"] == []
    name = _vendor()
    body = client.get("/api/vendor-documents").get_json()
    assert [v["name"] for v in body["vendors"]] == [name]
    # A vendor with nothing filed against it still gets an (empty) shelf.
    assert body["documents"][body["vendors"][0]["vendor_id"]] == []


def test_upload_list_download_delete(client):
    vendor_id = _vendor_id(client, _vendor())
    upload = _upload(client, vendor_id)
    assert upload.status_code == 201
    doc = upload.get_json()[0]
    assert doc["original_name"] == "contract.pdf"
    assert doc["description"] == "Master agreement"

    listed = client.get("/api/vendor-documents").get_json()
    assert len(listed["documents"][vendor_id]) == 1

    download = client.get(
        "/api/vendor-documents/" + vendor_id + "/" + doc["item_id"] + "/download")
    assert download.status_code == 200 and download.data == b"PDFDATA"

    deleted = client.post(
        "/api/vendor-documents/" + vendor_id + "/" + doc["item_id"] + "/delete",
        headers=HEADERS)
    assert deleted.get_json() == []


def test_each_vendor_keeps_its_own_documents(client):
    first = _vendor_id(client, _vendor("Acme Analytics"))
    second = _vendor_id(client, _vendor("Beta Data"))
    _upload(client, first, "acme.pdf")
    _upload(client, second, "beta.pdf")
    docs = client.get("/api/vendor-documents").get_json()["documents"]
    assert [d["original_name"] for d in docs[first]] == ["acme.pdf"]
    assert [d["original_name"] for d in docs[second]] == ["beta.pdf"]


def test_upload_to_an_undeclared_vendor_is_404(client):
    assert _upload(client, "VN-999").status_code == 404


def test_no_file_is_400(client):
    vendor_id = _vendor_id(client, _vendor())
    response = client.post("/api/vendor-documents/" + vendor_id, data={},
                           content_type="multipart/form-data", headers=HEADERS)
    assert response.status_code == 400


def test_bad_extension_is_400(client):
    vendor_id = _vendor_id(client, _vendor())
    assert _upload(client, vendor_id, "evil.exe").status_code == 400


def test_download_unknown_is_404(client):
    vendor_id = _vendor_id(client, _vendor())
    assert client.get(
        "/api/vendor-documents/" + vendor_id + "/DOC-999/download").status_code == 404


def test_download_missing_file_is_404(client):
    vendor_id = _vendor_id(client, _vendor())
    doc = _upload(client, vendor_id).get_json()[0]
    upload_path("vendor/" + vendor_id, doc["filename"]).unlink()
    assert client.get(
        "/api/vendor-documents/" + vendor_id + "/" + doc["item_id"] +
        "/download").status_code == 404


def test_delete_unknown_is_404(client):
    vendor_id = _vendor_id(client, _vendor())
    assert client.post("/api/vendor-documents/" + vendor_id + "/DOC-999/delete",
                       headers=HEADERS).status_code == 404
