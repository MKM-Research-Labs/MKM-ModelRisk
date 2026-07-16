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
"""Tests for the bibliography HTTP API."""
from __future__ import annotations

from tests.web.conftest import HEADERS


def _add(client, fields):
    return client.post(
        "/api/bibliography/references", json={"fields": fields, "confirmed": True}, headers=HEADERS,
    )


def test_list_includes_spec(client):
    result = client.get("/api/bibliography").get_json()
    assert any(f["key"] == "authors" for f in result["spec"]["fields"])
    assert result["references"] == []


def test_add_update_remove(client):
    added = _add(client, {"authors": "Kelly, D.", "title": "Handbook", "year": "2025"})
    assert added.status_code == 201
    item = added.get_json()[0]["item_id"]

    updated = client.post(
        "/api/bibliography/references/" + item,
        json={"fields": {"category": "Governance"}, "confirmed": True}, headers=HEADERS,
    )
    assert updated.get_json()[0]["category"] == "Governance"

    removed = client.post(
        "/api/bibliography/references/" + item + "/delete",
        json={"confirmed": True}, headers=HEADERS,
    )
    assert removed.get_json() == []


def test_add_missing_required_is_400(client):
    assert _add(client, {"authors": "Kelly, D."}).status_code == 400


def test_export_bibtex(client):
    _add(client, {"authors": "Kelly, D.", "title": "Handbook"})
    response = client.get("/api/bibliography/export.bib")
    assert response.status_code == 200
    assert b"@misc{" in response.data
    assert "application/x-bibtex" in response.content_type
