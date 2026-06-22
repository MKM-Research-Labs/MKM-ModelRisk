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
"""Tests for the reference-data HTTP API and model-field dropdown enrichment."""
from __future__ import annotations

from tests.web.conftest import HEADERS


def _company_field(client):
    specs = client.get("/api/models/fields").get_json()
    return next(f for g in specs["groups"] for f in g["fields"] if f["key"] == "company")


def test_get_reference_empty(client):
    res = client.get("/api/reference").get_json()
    assert res["data"] == {"company": [], "division": [], "department": []}
    assert [c["key"] for c in res["collections"]] == ["company", "division", "department"]


def test_add_and_remove_option(client):
    add = client.post(
        "/api/reference/collections/company",
        json={"fields": {"value": "MKM Bank"}, "confirmed": True}, headers=HEADERS,
    )
    assert add.status_code == 201
    item = add.get_json()["company"][0]
    assert item["value"] == "MKM Bank"

    removed = client.post(
        "/api/reference/collections/company/" + item["item_id"] + "/delete",
        json={"confirmed": True}, headers=HEADERS,
    )
    assert removed.get_json()["company"] == []


def test_add_missing_value_is_400(client):
    response = client.post(
        "/api/reference/collections/company",
        json={"fields": {}, "confirmed": True}, headers=HEADERS,
    )
    assert response.status_code == 400


def test_add_unknown_list_is_400(client):
    response = client.post(
        "/api/reference/collections/nope",
        json={"fields": {"value": "x"}, "confirmed": True}, headers=HEADERS,
    )
    assert response.status_code == 400


def test_add_without_confirmation_is_409(client):
    response = client.post(
        "/api/reference/collections/company",
        json={"fields": {"value": "x"}}, headers=HEADERS,
    )
    assert response.status_code == 409


def test_model_company_field_becomes_dropdown_after_adding(client):
    assert _company_field(client)["type"] == "text"
    client.post(
        "/api/reference/collections/company",
        json={"fields": {"value": "MKM Bank"}, "confirmed": True}, headers=HEADERS,
    )
    enriched = _company_field(client)
    assert enriched["type"] == "choice"
    assert enriched["options"] == ["MKM Bank"]
