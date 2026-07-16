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
"""Tests for products-in-scope on a meeting: set / join / analysis document —
the product mirror of the models-in-scope endpoints."""
from __future__ import annotations

import io

from src.files import upload_path
from tests.web.conftest import HEADERS


def _upload(client, name="analysis.pdf", data=b"analysis-pdf"):
    return client.post(
        "/api/meetings/MTG1/products/P1/analysis",
        data={"file": (io.BytesIO(data), name)},
        content_type="multipart/form-data", headers=HEADERS,
    )


def _model(client, model_id="M1"):
    return client.post(
        "/api/models",
        json={"model_id": model_id, "name": "Analytics", "confirmed": True,
              "fields": {"tier": 2, "rag_rating": "Green", "next_review_date": "2020-01-01"}},
        headers=HEADERS,
    )


def _product(client, product_id="P1", name="Bond Fund"):
    return client.post(
        "/api/products",
        json={"product_id": product_id, "product": name, "confirmed": True,
              "fields": {"analytics_model": "M1", "market_data_model": "m", "calculating_agent": "c"}},
        headers=HEADERS,
    )


def _schedule(client, meeting_id="MTG1"):
    return client.post(
        "/api/meetings",
        json={"meeting_id": meeting_id, "title": "Q2", "date": "2026-06-30", "confirmed": True},
        headers=HEADERS,
    )


def _set(client, product_ids, confirmed=True):
    body = {"product_ids": product_ids}
    if confirmed:
        body["confirmed"] = True
    return client.post(
        "/api/meetings/MTG1/collections/products_in_scope/set", json=body, headers=HEADERS,
    )


def _scope_ids(client):
    return {r["product_id"] for r in client.get("/api/meetings/MTG1/products").get_json()}


def test_products_in_scope_joins_register(client):
    _model(client)
    _product(client)
    # The product's own risk rating + review date drive the joined row.
    client.post("/api/products/P1/field",
                json={"field": "rag_rating", "value": "Green", "confirmed": True}, headers=HEADERS)
    client.post("/api/products/P1/field",
                json={"field": "next_review_date", "value": "2020-01-01"}, headers=HEADERS)
    _schedule(client)
    _set(client, ["P1"])
    rows = client.get("/api/meetings/MTG1/products").get_json()
    assert rows[0]["product_id"] == "P1"
    assert rows[0]["name"] == "Bond Fund"
    assert rows[0]["rag_rating"] == "Green"
    assert rows[0]["review_status"] == "Overdue"


def test_products_in_scope_handles_unknown_product(client):
    _schedule(client)
    client.post("/api/meetings/MTG1/collections/products_in_scope",
                json={"fields": {"product_id": "GHOST"}, "confirmed": True}, headers=HEADERS)
    rows = client.get("/api/meetings/MTG1/products").get_json()
    assert rows[0]["product_id"] == "GHOST" and rows[0]["name"] is None
    assert rows[0]["review_status"] == "Not Scheduled"


def test_products_endpoint_unknown_meeting_is_404(client):
    assert client.get("/api/meetings/none/products").status_code == 404


def test_set_products_in_scope_adds_and_removes(client):
    _model(client)
    _product(client, "P1", "Bond Fund")
    _product(client, "P2", "Equity Fund")
    _schedule(client)
    _set(client, ["P1", "P2"])
    assert _scope_ids(client) == {"P1", "P2"}
    _set(client, ["P2"])   # drop P1
    assert _scope_ids(client) == {"P2"}


def test_set_products_in_scope_unknown_meeting_is_404(client):
    resp = client.post("/api/meetings/NOPE/collections/products_in_scope/set",
                       json={"product_ids": ["P1"], "confirmed": True}, headers=HEADERS)
    assert resp.status_code == 404


def test_set_products_in_scope_applies_without_confirmation(client):
    _model(client)
    _product(client)
    _schedule(client)
    assert _set(client, ["P1"], confirmed=False).status_code == 200
    assert _scope_ids(client) == {"P1"}


def test_upload_and_download_product_analysis(client):
    _model(client)
    _product(client)
    _schedule(client)
    _set(client, ["P1"])
    assert _upload(client).status_code == 201
    dl = client.get("/api/meetings/MTG1/products/P1/analysis")
    assert dl.status_code == 200 and dl.data == b"analysis-pdf"


def test_upload_product_analysis_not_in_scope_is_400(client):
    _model(client)
    _product(client)
    _schedule(client)
    assert _upload(client).status_code == 400


def test_upload_product_analysis_unknown_meeting_is_404(client):
    up = client.post(
        "/api/meetings/NOPE/products/P1/analysis",
        data={"file": (io.BytesIO(b"x"), "a.pdf")},
        content_type="multipart/form-data", headers=HEADERS,
    )
    assert up.status_code == 404


def test_upload_product_analysis_no_file_is_400(client):
    _model(client)
    _product(client)
    _schedule(client)
    _set(client, ["P1"])
    resp = client.post("/api/meetings/MTG1/products/P1/analysis",
                       data={}, content_type="multipart/form-data", headers=HEADERS)
    assert resp.status_code == 400 and "no file" in resp.get_json()["error"]


def test_upload_product_analysis_bad_type_is_400(client):
    _model(client)
    _product(client)
    _schedule(client)
    _set(client, ["P1"])
    assert _upload(client, name="malware.exe").status_code == 400


def test_download_product_analysis_missing_is_404(client):
    _model(client)
    _product(client)
    _schedule(client)
    _set(client, ["P1"])
    assert client.get("/api/meetings/MTG1/products/P1/analysis").status_code == 404


def test_download_product_analysis_file_gone_from_disk_is_404(client):
    _model(client)
    _product(client)
    _schedule(client)
    _set(client, ["P1"])
    _upload(client)
    meeting = client.get("/api/meetings/MTG1").get_json()
    item = next(i for i in meeting["data"]["products_in_scope"] if i["product_id"] == "P1")
    upload_path("meeting_analysis", item["analysis_filename"]).unlink()
    assert client.get("/api/meetings/MTG1/products/P1/analysis").status_code == 404
