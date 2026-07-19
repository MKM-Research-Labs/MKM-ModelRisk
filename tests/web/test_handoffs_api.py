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
"""Tests for the model-handoff HTTP API."""
from __future__ import annotations

from tests.web.conftest import HEADERS


def _register(client, model_id, name=None):
    return client.post(
        "/api/models",
        json={"model_id": model_id, "name": name or model_id, "confirmed": True},
        headers=HEADERS,
    )


def _edge(client, from_model, to_model):
    _register(client, from_model)
    _register(client, to_model)
    return client.post(
        f"/api/models/{from_model}/collections/dependencies",
        json={"fields": {"direction": "downstream", "model_id": to_model}, "confirmed": True},
        headers=HEADERS,
    )


def _declare(client, from_model, to_model):
    return client.post(
        "/api/handoffs",
        json={"from_model": from_model, "to_model": to_model, "confirmed": True},
        headers=HEADERS,
    )


def test_declare_handoff_on_an_edge_then_get(client):
    _edge(client, "A", "B")
    created = _declare(client, "A", "B")
    assert created.status_code == 201
    hid = created.get_json()["handoff_id"]
    assert hid == "A~B"
    got = client.get(f"/api/handoffs/{hid}").get_json()
    assert got["data"]["from_model"] == "A" and got["data"]["status"] == "Draft"


def test_declaring_twice_returns_the_existing_handoff(client):
    _edge(client, "A", "B")
    assert _declare(client, "A", "B").status_code == 201
    again = _declare(client, "A", "B")
    assert again.status_code == 200  # idempotent: returns the existing one, not a 400


def test_declare_on_a_non_edge_is_400(client):
    _register(client, "A")
    _register(client, "B")  # both exist, but no A->B dependency
    resp = _declare(client, "A", "B")
    assert resp.status_code == 400
    assert "no declared dependency" in resp.get_json()["error"]


def test_field_lineage_crud_through_the_api(client):
    _edge(client, "A", "B")
    _declare(client, "A", "B")
    add = client.post(
        "/api/handoffs/A~B/collections/field_lineage",
        json={"fields": {"provider_field": "spread", "provider_type": "float",
                         "consumer_field": "spread_in", "consumer_type": "float"},
              "confirmed": True},
        headers=HEADERS,
    )
    assert add.status_code == 201
    item = add.get_json()["data"]["field_lineage"][0]
    assert item["provider_field"] == "spread" and item["consumer_field"] == "spread_in"

    client.post(
        f"/api/handoffs/A~B/collections/field_lineage/{item['item_id']}",
        json={"fields": {"consumer_units": "percent"}, "confirmed": True}, headers=HEADERS,
    )
    delete = client.post(
        f"/api/handoffs/A~B/collections/field_lineage/{item['item_id']}/delete",
        json={"confirmed": True}, headers=HEADERS,
    )
    assert delete.get_json()["data"]["field_lineage"] == []


def test_compatibility_note_is_editable(client):
    _edge(client, "A", "B")
    _declare(client, "A", "B")
    resp = client.post(
        "/api/handoffs/A~B/field",
        json={"field": "compatibility", "value": "units aligned", "confirmed": True},
        headers=HEADERS,
    )
    assert resp.get_json()["data"]["compatibility"] == "units aligned"


def test_get_unknown_handoff_is_404(client):
    assert client.get("/api/handoffs/none~gone").status_code == 404


def test_list_handoffs(client):
    _edge(client, "A", "B")
    _declare(client, "A", "B")
    listing = client.get("/api/handoffs").get_json()
    assert [h["handoff_id"] for h in listing] == ["A~B"]


def test_handover_pdf_is_served(client, monkeypatch):
    # Stub the LaTeX compile so the endpoint is exercised without tectonic.
    from src.governance.model_handoff import document
    monkeypatch.setattr(document, "compile_tex", lambda tex, assets=None: b"%PDF-stub")
    _edge(client, "A", "B")
    _declare(client, "A", "B")
    res = client.get("/api/handoffs/A~B/handover.pdf")
    assert res.status_code == 200
    assert res.mimetype == "application/pdf"
    assert res.data.startswith(b"%PDF")


def test_handover_pdf_is_503_without_tectonic(client, monkeypatch):
    from src.governance.mrc import pack
    monkeypatch.setattr(pack.shutil, "which", lambda _name: None)
    _edge(client, "A", "B")
    _declare(client, "A", "B")
    res = client.get("/api/handoffs/A~B/handover.pdf")
    assert res.status_code == 503
    assert "tectonic" in res.get_json()["error"]


def test_handover_pdf_unknown_handoff_is_404(client):
    assert client.get("/api/handoffs/no~such/handover.pdf").status_code == 404
