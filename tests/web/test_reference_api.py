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


def _model_field(client, key):
    specs = client.get("/api/models/fields").get_json()
    return next(f for g in specs["groups"] for f in g["fields"] if f["key"] == key)


def _meeting_field(client, key):
    specs = client.get("/api/meetings/fields").get_json()
    return next(f for f in specs["fields"] if f["key"] == key)


def _add_person(client, name):
    return client.post(
        "/api/reference/collections/people",
        json={"fields": {"name": name, "role": "Owner"}, "confirmed": True}, headers=HEADERS,
    )


def test_get_reference_empty(client):
    res = client.get("/api/reference").get_json()
    assert res["data"] == {"company": [], "division": [], "department": [],
                           "calculating_agent": [], "mrc": [], "people": []}
    assert [c["key"] for c in res["collections"]] == [
        "company", "division", "department", "mrc", "calculating_agent", "people"]


def test_update_company_via_api(client):
    client.post("/api/reference/collections/company",
                json={"fields": {"value": "MKM Bank"}, "confirmed": True}, headers=HEADERS)
    res = client.post("/api/reference/collections/company/CO-001",
                      json={"fields": {"owner": "jane@firm"}, "confirmed": True}, headers=HEADERS)
    assert res.status_code == 200
    assert res.get_json()["company"][0]["owner"] == "jane@firm"


def test_division_company_field_becomes_dropdown(client):
    # Once a company exists, the Division form's Company field is a dropdown.
    client.post("/api/reference/collections/company",
                json={"fields": {"value": "MKM Bank"}, "confirmed": True}, headers=HEADERS)
    res = client.get("/api/reference").get_json()
    division = next(c for c in res["collections"] if c["key"] == "division")
    company_field = next(f for f in division["fields"] if f["key"] == "company")
    assert company_field["type"] == "choice"
    assert "MKM Bank" in company_field["options"]


def test_add_and_remove_person(client):
    added = _add_person(client, "Jane Doe")
    assert added.status_code == 201
    person = added.get_json()["people"][0]
    assert person["name"] == "Jane Doe"
    removed = client.post(
        "/api/reference/collections/people/" + person["item_id"] + "/delete",
        json={"confirmed": True}, headers=HEADERS,
    )
    assert removed.get_json()["people"] == []


def test_owner_and_chair_become_people_dropdowns(client):
    assert _model_field(client, "owner")["type"] == "text"
    assert _meeting_field(client, "chair")["type"] == "text"
    _add_person(client, "Jane Doe")
    owner = _model_field(client, "owner")
    chair = _meeting_field(client, "chair")
    assert owner["type"] == "choice" and owner["options"] == ["Jane Doe"]
    assert chair["type"] == "choice" and chair["options"] == ["Jane Doe"]


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
    assert _model_field(client, "company")["type"] == "text"
    client.post(
        "/api/reference/collections/company",
        json={"fields": {"value": "MKM Bank"}, "confirmed": True}, headers=HEADERS,
    )
    enriched = _model_field(client, "company")
    assert enriched["type"] == "choice"
    assert enriched["options"] == ["MKM Bank"]
