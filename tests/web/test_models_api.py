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
"""Tests for the model-inventory HTTP API."""
from __future__ import annotations

from tests.web.conftest import HEADERS


def _register(client, model_id="M1", name="Alpha", **fields):
    return client.post(
        "/api/models",
        json={"model_id": model_id, "name": name, "fields": fields, "confirmed": True},
        headers=HEADERS,
    )


def test_register_then_list_and_get(client):
    response = _register(client, tier=2, owner="bob")
    assert response.status_code == 201
    assert response.get_json()["data"]["name"] == "Alpha"

    listing = client.get("/api/models").get_json()
    assert [m["model_id"] for m in listing] == ["M1"]

    one = client.get("/api/models/M1").get_json()
    assert one["data"]["owner"] == "bob"
    assert one["data"]["tier"] == 2


def test_get_unknown_model_is_404(client):
    assert client.get("/api/models/none").status_code == 404


def test_update_field_records_actor(client):
    _register(client)
    response = client.post(
        "/api/models/M1/field",
        json={"field": "owner", "value": "carol", "confirmed": True},
        headers={"X-Auth-Request-User": "carol@corp"},
    )
    assert response.status_code == 200
    assert response.get_json()["data"]["owner"] == "carol"


def test_retire_marks_model(client):
    _register(client)
    response = client.post("/api/models/M1/retire", json={"confirmed": True}, headers=HEADERS)
    assert response.status_code == 200
    assert response.get_json()["retired"] is True


def test_mutation_without_confirmation_is_409(client):
    response = client.post(
        "/api/models",
        json={"model_id": "M1", "name": "Alpha"},  # no confirmed flag
        headers=HEADERS,
    )
    assert response.status_code == 409
    assert response.get_json()["needs_confirmation"] is True
    # Nothing was written.
    assert client.get("/api/models").get_json() == []


def test_domain_error_is_400(client):
    _register(client)
    response = _register(client)  # duplicate
    assert response.status_code == 400
    assert "already registered" in response.get_json()["error"]


def test_invalid_field_value_is_400(client):
    _register(client)
    response = client.post(
        "/api/models/M1/field",
        json={"field": "rag_rating", "value": "Purple", "confirmed": True},
        headers=HEADERS,
    )
    assert response.status_code == 400
