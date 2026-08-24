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


def test_upload_with_model_types_then_edit(client):
    up = client.post(
        "/api/documents",
        data={"file": (io.BytesIO(b"PDFDATA"), "cyclones.pdf"),
              "model_types": ["Hazard", "Regulatory"]},
        content_type="multipart/form-data", headers=HEADERS,
    )
    assert up.status_code == 201
    doc = up.get_json()[0]
    assert doc["model_types"] == ["Hazard", "Regulatory"]

    # Edit the tags via the metadata-only endpoint (file and id survive).
    edited = client.post(
        "/api/documents/" + doc["item_id"] + "/model-types",
        json={"model_types": ["Pricing", "Pricing", " "]}, headers=HEADERS)
    assert edited.status_code == 200
    after = edited.get_json()[0]
    assert after["item_id"] == doc["item_id"]
    assert after["model_types"] == ["Pricing"]


def test_set_model_types_on_unknown_is_404(client):
    resp = client.post("/api/documents/DOC-999/model-types",
                       json={"model_types": ["Hazard"]}, headers=HEADERS)
    assert resp.status_code == 404


def test_upload_keeps_the_description_it_was_given(client):
    assert _upload(client).get_json()[0]["description"] == "Q1 pack"


def test_metadata_amends_description_and_tags_together(client):
    doc = _upload(client).get_json()[0]
    resp = client.post("/api/documents/" + doc["item_id"] + "/metadata",
                       json={"description": "  Q1 board pack  ",
                             "model_types": ["Regulatory"]}, headers=HEADERS)
    assert resp.status_code == 200
    after = resp.get_json()[0]
    assert after["item_id"] == doc["item_id"], "the file and its id stay put"
    assert after["description"] == "Q1 board pack"
    assert after["model_types"] == ["Regulatory"]


def test_amending_one_field_leaves_the_other_alone(client):
    """The older ``/model-types`` path knows nothing about the description, so
    omission must mean "unchanged" rather than "cleared"."""
    doc = _upload(client).get_json()[0]
    after = client.post("/api/documents/" + doc["item_id"] + "/model-types",
                        json={"model_types": ["Hazard"]}, headers=HEADERS).get_json()[0]
    assert after["description"] == "Q1 pack" and after["model_types"] == ["Hazard"]

    cleared = client.post("/api/documents/" + doc["item_id"] + "/metadata",
                          json={"description": ""}, headers=HEADERS).get_json()[0]
    assert cleared["description"] == "", "an explicit empty description does clear it"
    assert cleared["model_types"] == ["Hazard"]


def test_metadata_with_nothing_to_amend_is_400(client):
    doc = _upload(client).get_json()[0]
    resp = client.post("/api/documents/" + doc["item_id"] + "/metadata",
                       json={}, headers=HEADERS)
    assert resp.status_code == 400
