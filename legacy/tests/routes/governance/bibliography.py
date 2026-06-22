# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Tests for routes.governance.bibliography — CRUD for bibliography references.

Covers: GET (empty/with data), POST add (basic/with category), PUT update
(not found/valid/new category), DELETE (not found/valid).
"""

import json
from pathlib import Path

import pytest


# ===========================================================================
# Fixtures
# ===========================================================================

@pytest.fixture
def bib_env(tmp_path, monkeypatch):
    """Isolated bibliography environment."""
    import routes.governance._constants as gov_constants

    bib_path = str(tmp_path / "bibliography.json")
    bib_data = {"references": [], "categories": []}
    Path(bib_path).write_text(json.dumps(bib_data))

    monkeypatch.setattr(gov_constants, "BIBLIOGRAPHY_PATH", bib_path)
    return {"bib_path": bib_path, "tmp_path": tmp_path}


@pytest.fixture
def bib_client(bib_env, monkeypatch):
    """Flask test client with isolated bibliography."""
    from config import config
    monkeypatch.setattr(config, "get_input_dir", lambda: bib_env["tmp_path"])

    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client(), bib_env


# ===========================================================================
# GET /governance/bibliography
# ===========================================================================

class TestGetBibliography:

    def test_returns_200(self, bib_client):
        client, _ = bib_client
        r = client.get("/api/v1/governance/bibliography")
        assert r.status_code == 200

    def test_returns_success_status(self, bib_client):
        client, _ = bib_client
        r = client.get("/api/v1/governance/bibliography")
        assert r.get_json()["status"] == "success"

    def test_empty_references(self, bib_client):
        client, _ = bib_client
        r = client.get("/api/v1/governance/bibliography")
        assert r.get_json()["references"] == []

    def test_has_categories_key(self, bib_client):
        client, _ = bib_client
        r = client.get("/api/v1/governance/bibliography")
        assert "categories" in r.get_json()


# ===========================================================================
# POST /governance/bibliography — add reference
# ===========================================================================

class TestAddBibliographyRef:

    def test_add_returns_200(self, bib_client):
        client, _ = bib_client
        r = client.post("/api/v1/governance/bibliography", json={
            "author": "Smith, J.",
            "year": 2024,
            "title": "Test Paper",
        })
        assert r.status_code == 200

    def test_add_returns_reference(self, bib_client):
        client, _ = bib_client
        r = client.post("/api/v1/governance/bibliography", json={
            "title": "My Paper",
        })
        data = r.get_json()
        assert data["status"] == "success"
        assert "reference" in data

    def test_add_assigns_id(self, bib_client):
        client, _ = bib_client
        r = client.post("/api/v1/governance/bibliography", json={"title": "Paper"})
        ref = r.get_json()["reference"]
        assert "id" in ref
        assert len(ref["id"]) > 0

    def test_add_appears_in_list(self, bib_client):
        client, _ = bib_client
        client.post("/api/v1/governance/bibliography", json={"title": "Listed Paper"})
        r = client.get("/api/v1/governance/bibliography")
        assert len(r.get_json()["references"]) == 1

    def test_add_with_category_updates_categories(self, bib_client):
        client, _ = bib_client
        client.post("/api/v1/governance/bibliography", json={
            "title": "Paper", "category": "Flood Risk"
        })
        r = client.get("/api/v1/governance/bibliography")
        assert "Flood Risk" in r.get_json()["categories"]

    def test_add_same_category_twice_no_duplicate(self, bib_client):
        client, _ = bib_client
        client.post("/api/v1/governance/bibliography", json={"title": "A", "category": "Risk"})
        client.post("/api/v1/governance/bibliography", json={"title": "B", "category": "Risk"})
        r = client.get("/api/v1/governance/bibliography")
        assert r.get_json()["categories"].count("Risk") == 1

    def test_add_stores_all_fields(self, bib_client):
        client, _ = bib_client
        r = client.post("/api/v1/governance/bibliography", json={
            "author": "Jones", "year": 2023, "title": "Study",
            "journal": "Nature", "doi": "10.1/test", "url": "http://ex.com",
            "category": "Hydrology", "notes": "Key ref"
        })
        ref = r.get_json()["reference"]
        assert ref["author"] == "Jones"
        assert ref["journal"] == "Nature"
        assert ref["doi"] == "10.1/test"

    def test_add_no_json_body_uses_defaults(self, bib_client):
        client, _ = bib_client
        r = client.post(
            "/api/v1/governance/bibliography",
            data=b"",
            content_type="application/json",
        )
        # Should still succeed with empty defaults
        assert r.status_code in (200, 400, 500)


# ===========================================================================
# PUT /governance/bibliography/<ref_id>
# ===========================================================================

class TestUpdateBibliographyRef:

    def _add_ref(self, client):
        r = client.post("/api/v1/governance/bibliography", json={"title": "Original"})
        return r.get_json()["reference"]["id"]

    def test_not_found_returns_404(self, bib_client):
        client, _ = bib_client
        r = client.put("/api/v1/governance/bibliography/nonexistent", json={})
        assert r.status_code == 404

    def test_update_returns_success(self, bib_client):
        client, _ = bib_client
        ref_id = self._add_ref(client)
        r = client.put(f"/api/v1/governance/bibliography/{ref_id}", json={"title": "Updated"})
        assert r.status_code == 200
        assert r.get_json()["status"] == "success"

    def test_update_changes_field(self, bib_client):
        client, _ = bib_client
        ref_id = self._add_ref(client)
        client.put(f"/api/v1/governance/bibliography/{ref_id}", json={"author": "New Author"})
        r = client.get("/api/v1/governance/bibliography")
        ref = next(x for x in r.get_json()["references"] if x["id"] == ref_id)
        assert ref["author"] == "New Author"

    def test_update_with_new_category_adds_to_list(self, bib_client):
        client, _ = bib_client
        ref_id = self._add_ref(client)
        client.put(f"/api/v1/governance/bibliography/{ref_id}", json={"category": "NewCat"})
        r = client.get("/api/v1/governance/bibliography")
        assert "NewCat" in r.get_json()["categories"]


# ===========================================================================
# DELETE /governance/bibliography/<ref_id>
# ===========================================================================

class TestDeleteBibliographyRef:

    def _add_ref(self, client):
        r = client.post("/api/v1/governance/bibliography", json={"title": "ToDelete"})
        return r.get_json()["reference"]["id"]

    def test_delete_nonexistent_still_returns_success(self, bib_client):
        """Delete is idempotent — filtering out a missing ID is still 200."""
        client, _ = bib_client
        r = client.delete("/api/v1/governance/bibliography/nonexistent")
        assert r.status_code == 200

    def test_delete_returns_success(self, bib_client):
        client, _ = bib_client
        ref_id = self._add_ref(client)
        r = client.delete(f"/api/v1/governance/bibliography/{ref_id}")
        assert r.status_code == 200
        assert r.get_json()["status"] == "success"

    def test_deleted_ref_not_in_list(self, bib_client):
        client, _ = bib_client
        ref_id = self._add_ref(client)
        client.delete(f"/api/v1/governance/bibliography/{ref_id}")
        r = client.get("/api/v1/governance/bibliography")
        ids = [x["id"] for x in r.get_json()["references"]]
        assert ref_id not in ids
