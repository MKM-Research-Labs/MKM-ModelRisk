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
