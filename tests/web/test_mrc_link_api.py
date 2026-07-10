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


def _register_product(client, product_id="P-1", analytics_model="M1", **org):
    resp = client.post(
        "/api/products",
        json={"product_id": product_id, "product": "Bond",
              "fields": {"analytics_model": analytics_model,
                         "market_data_model": "m", "calculating_agent": "c"},
              "confirmed": True},
        headers=HEADERS,
    )
    # Org fields (division/department) are set via the detail field editor.
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
    _register_product(client, analytics_model="M1", division="Markets")
    res = client.get("/api/products/P-1/mrc").get_json()
    assert res["mrc"]["value"] == "MRC-MKT"
    assert res["level"] == "Division"


def test_product_mrc_none_when_org_unmatched(client):
    _register_model(client, model_id="M1")
    _register_product(client, analytics_model="M1", division="Nowhere")
    res = client.get("/api/products/P-1/mrc").get_json()
    assert res["mrc"] is None and res["level"] is None
