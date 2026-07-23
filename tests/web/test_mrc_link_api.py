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
"""The model/product → responsible-MRC derivation endpoints (``/mrc``)."""
from __future__ import annotations

from tests.web.conftest import HEADERS


def _seed_mrc(client, value, level, scope_value=None):
    fields = {"value": value, "name": value, "level": level}
    if scope_value:
        fields["scope_value"] = scope_value
    return client.post(
        "/api/reference/collections/mrc",
        json={"fields": fields, "confirmed": True}, headers=HEADERS,
    )


def _register_model(client, model_id="M1", **fields):
    return client.post(
        "/api/models",
        json={"model_id": model_id, "name": "Model", "fields": fields, "confirmed": True},
        headers=HEADERS,
    )


def _register_product(client, product_id="P-1", **org):
    resp = client.post(
        "/api/products",
        json={"product_id": product_id, "product": "Bond",
              "fields": {"calculating_agent": "c"},
              "confirmed": True},
        headers=HEADERS,
    )
    # Org fields (division / line of business) are set via the detail field editor.
    for field, value in org.items():
        client.post(f"/api/products/{product_id}/field",
                    json={"field": field, "value": value, "confirmed": True}, headers=HEADERS)
    return resp


# ------------------------------------------------------------- model /mrc ----

def test_model_mrc_matches_company_level(client):
    _seed_mrc(client, "MRC-CO", "Company")
    _register_model(client)
    res = client.get("/api/models/M1/mrc").get_json()
    assert res["level"] == "Company" and res["mrc"]["value"] == "MRC-CO"


def test_model_mrc_prefers_division_over_company(client):
    _seed_mrc(client, "MRC-CO", "Company")
    _seed_mrc(client, "MRC-MKT", "Division", scope_value="Markets")
    _register_model(client, division="Markets")
    res = client.get("/api/models/M1/mrc").get_json()
    assert res["level"] == "Division" and res["mrc"]["value"] == "MRC-MKT"


def test_model_mrc_none_when_unmatched(client):
    _register_model(client, division="Nowhere")
    res = client.get("/api/models/M1/mrc").get_json()
    assert res["mrc"] is None and res["level"] is None


def test_model_mrc_unknown_model_is_404(client):
    assert client.get("/api/models/NOPE/mrc").status_code == 404


# ----------------------------------------------------------- product /mrc ----

def test_product_mrc_from_own_division(client):
    # The product's own Division drives its MRC — the analytics model's org is
    # irrelevant (here the model has none).
    _seed_mrc(client, "MRC-CO", "Company")
    _seed_mrc(client, "MRC-MKT", "Division", scope_value="Markets")
    _register_model(client, model_id="M1")
    _register_product(client, division="Markets")
    res = client.get("/api/products/P-1/mrc").get_json()
    assert res["mrc"]["value"] == "MRC-MKT"
    assert res["level"] == "Division"


def test_product_mrc_none_when_org_unmatched(client):
    _register_model(client, model_id="M1")
    _register_product(client, division="Nowhere")
    res = client.get("/api/products/P-1/mrc").get_json()
    assert res["mrc"] is None and res["level"] is None
