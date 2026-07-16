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
"""Tests for the structured-collection HTTP API."""
from __future__ import annotations

from tests.web.conftest import HEADERS


def _register(client):
    client.post(
        "/api/models",
        json={"model_id": "M1", "name": "Alpha", "confirmed": True},
        headers=HEADERS,
    )


def _add(client, collection, fields):
    return client.post(
        "/api/models/M1/collections/" + collection,
        json={"fields": fields, "confirmed": True},
        headers=HEADERS,
    )


def test_collection_specs_in_fields(client):
    specs = client.get("/api/models/fields").get_json()
    keys = [c["key"] for c in specs["collections"]]
    assert "assumptions" in keys and "validation_questions" in keys
    assumptions = next(c for c in specs["collections"] if c["key"] == "assumptions")
    desc = next(f for f in assumptions["fields"] if f["key"] == "description")
    assert desc["required"] is True
    impact = next(f for f in assumptions["fields"] if f["key"] == "impact")
    assert impact["type"] == "choice" and "High" in impact["options"]


def test_add_then_remove_collection_item(client):
    _register(client)
    response = _add(client, "assumptions", {"description": "Rates stable", "impact": "High"})
    assert response.status_code == 201
    assumptions = response.get_json()["data"]["assumptions"]
    assert assumptions[0]["item_id"] == "AS-001"
    assert assumptions[0]["impact"] == "High"

    delete = client.post(
        "/api/models/M1/collections/assumptions/AS-001/delete",
        json={"confirmed": True}, headers=HEADERS,
    )
    assert delete.get_json()["data"]["assumptions"] == []


def test_update_collection_item_status(client):
    _register(client)
    _add(client, "validation_questions", {"question": "Documented and approved?"})
    response = client.post(
        "/api/models/M1/collections/validation_questions/VQ-001",
        json={"fields": {"status": "Addressed"}, "confirmed": True}, headers=HEADERS,
    )
    assert response.get_json()["data"]["validation_questions"][0]["status"] == "Addressed"


def test_add_item_missing_required_is_400(client):
    _register(client)
    response = _add(client, "assumptions", {"impact": "High"})
    assert response.status_code == 400


def test_add_item_unknown_collection_is_400(client):
    _register(client)
    response = _add(client, "made_up", {"description": "x"})
    assert response.status_code == 400


def test_add_item_applies_without_confirmation(client):
    # Adding a non-critical collection item is not gated by confirm-to-amend.
    _register(client)
    response = client.post(
        "/api/models/M1/collections/assumptions",
        json={"fields": {"description": "x"}}, headers=HEADERS,
    )
    assert response.status_code == 201
    assert response.get_json()["data"]["assumptions"][0]["description"] == "x"
