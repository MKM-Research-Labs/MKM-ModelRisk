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
Tests for MRC meeting CRUD — agenda, minutes update, decisions.

Split from mrc_crud.py.
"""

import copy
import json
import pathlib

import pytest


_BASE_MEETING = {
    "id": "MRC-2026-001",
    "title": "Q1 2026 MRC Meeting",
    "date": "2026-03-15",
    "agenda": [
        {"item": 1, "title": "Minutes of previous meeting",
         "description": "", "presenter": "Chair",
         "duration": "10m", "status": "Standing"},
    ],
    "minutes": [
        {"item": 1, "title": "Minutes approved", "text": "Approved.",
         "presenter": "Chair"},
    ],
    "decisions": [
        {"id": "D-001", "description": "Approve GEV model", "date": "2026-03-15"},
    ],
    "actions": [
        {"id": "A-001", "description": "Update docs", "owner": "Lead",
         "target_date": "2026-04-01", "status": "Open"},
    ],
    "participants": [
        {"id": "P-001", "name": "Alice", "role": "CRO",
         "organisation": "MKM", "status": "Confirmed"},
    ],
}


@pytest.fixture
def mrc_crud_client(tmp_path, monkeypatch):
    """Flask test client with MRC meeting JSON and governance monkeypatches."""
    import routes.governance._constants as gov_constants
    from config import config

    meetings_path = str(tmp_path / "mrc_meetings.json")
    inv_path = str(tmp_path / "model_inventory.json")
    audit_path = str(tmp_path / "model_audit_log.json")

    with open(meetings_path, "w") as f:
        json.dump([copy.deepcopy(_BASE_MEETING)], f)
    with open(inv_path, "w") as f:
        json.dump({"models": []}, f)
    with open(audit_path, "w") as f:
        json.dump([], f)

    monkeypatch.setattr(gov_constants, "MRC_MEETINGS_PATH", meetings_path)
    monkeypatch.setattr(gov_constants, "INVENTORY_PATH", inv_path)
    monkeypatch.setattr(gov_constants, "AUDIT_LOG_PATH", audit_path)
    monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)

    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


BASE_URL = "/api/v1/governance/mrc/meetings/MRC-2026-001"


# ===========================================================================
# Agenda CRUD
# ===========================================================================

class TestAgendaCrud:

    def test_add_agenda_item_returns_200(self, mrc_crud_client):
        r = mrc_crud_client.post(
            f"{BASE_URL}/agenda",
            json={"title": "New Item", "presenter": "Speaker",
                  "status": "Presentation"},
        )
        assert r.status_code == 200
        assert r.get_json()["status"] == "success"

    def test_add_agenda_item_increments_count(self, mrc_crud_client):
        mrc_crud_client.post(f"{BASE_URL}/agenda",
                             json={"title": "Extra Item"})
        r = mrc_crud_client.post(f"{BASE_URL}/agenda",
                                  json={"title": "Another Item"})
        meeting = r.get_json()["meeting"]
        assert len(meeting["agenda"]) == 3  # 1 original + 2 new

    def test_add_agenda_missing_meeting_returns_404(self, mrc_crud_client):
        r = mrc_crud_client.post(
            "/api/v1/governance/mrc/meetings/GHOST/agenda",
            json={"title": "X"},
        )
        assert r.status_code == 404

    def test_update_agenda_item_returns_200(self, mrc_crud_client):
        r = mrc_crud_client.post(
            f"{BASE_URL}/agenda/1/update",
            json={"title": "Updated Title", "status": "Completed"},
        )
        assert r.status_code == 200
        meeting = r.get_json()["meeting"]
        assert meeting["agenda"][0]["title"] == "Updated Title"

    def test_update_agenda_item_not_found_returns_404(self, mrc_crud_client):
        r = mrc_crud_client.post(
            f"{BASE_URL}/agenda/999/update",
            json={"title": "X"},
        )
        assert r.status_code == 404

    def test_delete_agenda_item_returns_200(self, mrc_crud_client):
        # First add another item so there are 2
        mrc_crud_client.post(f"{BASE_URL}/agenda", json={"title": "Extra"})
        r = mrc_crud_client.post(f"{BASE_URL}/agenda/1/delete")
        assert r.status_code == 200
        meeting = r.get_json()["meeting"]
        # Should have renumbered the remaining item
        assert len(meeting["agenda"]) == 1
        assert meeting["agenda"][0]["item"] == 1

    def test_delete_agenda_missing_meeting_returns_404(self, mrc_crud_client):
        r = mrc_crud_client.post("/api/v1/governance/mrc/meetings/GHOST/agenda/1/delete")
        assert r.status_code == 404


# ===========================================================================
# Minutes update
# ===========================================================================

class TestMinutesUpdate:

    def test_update_minutes_returns_200(self, mrc_crud_client):
        r = mrc_crud_client.post(
            f"{BASE_URL}/minutes/update",
            json={"minutes": "New minutes text"},
        )
        assert r.status_code == 200
        assert r.get_json()["meeting"]["minutes"] == "New minutes text"

    def test_update_minutes_missing_meeting_returns_404(self, mrc_crud_client):
        r = mrc_crud_client.post(
            "/api/v1/governance/mrc/meetings/GHOST/minutes/update",
            json={"minutes": "x"},
        )
        assert r.status_code == 404


# ===========================================================================
# Decisions CRUD
# ===========================================================================

class TestDecisionsCrud:

    def test_add_decision_returns_200(self, mrc_crud_client):
        r = mrc_crud_client.post(
            f"{BASE_URL}/decisions",
            json={"description": "New decision", "date": "2026-03-15"},
        )
        assert r.status_code == 200
        meeting = r.get_json()["meeting"]
        assert len(meeting["decisions"]) == 2

    def test_add_decision_auto_ids(self, mrc_crud_client):
        r = mrc_crud_client.post(f"{BASE_URL}/decisions",
                                  json={"description": "D2"})
        decisions = r.get_json()["meeting"]["decisions"]
        ids = [d["id"] for d in decisions]
        assert "D-001" in ids
        assert "D-002" in ids

    def test_add_decision_missing_meeting_returns_404(self, mrc_crud_client):
        r = mrc_crud_client.post(
            "/api/v1/governance/mrc/meetings/GHOST/decisions",
            json={"description": "x"},
        )
        assert r.status_code == 404

    def test_update_decision_returns_200(self, mrc_crud_client):
        r = mrc_crud_client.post(
            f"{BASE_URL}/decisions/D-001/update",
            json={"description": "Updated decision"},
        )
        assert r.status_code == 200
        decisions = r.get_json()["meeting"]["decisions"]
        assert decisions[0]["description"] == "Updated decision"

    def test_update_decision_not_found_returns_404(self, mrc_crud_client):
        r = mrc_crud_client.post(
            f"{BASE_URL}/decisions/D-999/update",
            json={"description": "x"},
        )
        assert r.status_code == 404

    def test_delete_decision_returns_200(self, mrc_crud_client):
        r = mrc_crud_client.post(f"{BASE_URL}/decisions/D-001/delete")
        assert r.status_code == 200
        assert len(r.get_json()["meeting"]["decisions"]) == 0

    def test_delete_decision_missing_meeting_returns_404(self, mrc_crud_client):
        r = mrc_crud_client.post(
            "/api/v1/governance/mrc/meetings/GHOST/decisions/D-001/delete"
        )
        assert r.status_code == 404
