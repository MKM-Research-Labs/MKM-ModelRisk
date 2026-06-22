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
Tests for MRC meeting CRUD — actions, participants.

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
# Actions CRUD
# ===========================================================================

class TestActionsCrud:

    def test_add_action_returns_200(self, mrc_crud_client):
        r = mrc_crud_client.post(
            f"{BASE_URL}/actions",
            json={"description": "Do something", "owner": "Lead",
                  "target_date": "2026-05-01", "status": "Open"},
        )
        assert r.status_code == 200
        meeting = r.get_json()["meeting"]
        assert len(meeting["actions"]) == 2

    def test_add_action_auto_id(self, mrc_crud_client):
        r = mrc_crud_client.post(f"{BASE_URL}/actions",
                                  json={"description": "A2"})
        actions = r.get_json()["meeting"]["actions"]
        ids = [a["id"] for a in actions]
        assert "A-001" in ids
        assert "A-002" in ids

    def test_add_action_missing_meeting_returns_404(self, mrc_crud_client):
        r = mrc_crud_client.post(
            "/api/v1/governance/mrc/meetings/GHOST/actions",
            json={"description": "x"},
        )
        assert r.status_code == 404

    def test_update_action_returns_200(self, mrc_crud_client):
        r = mrc_crud_client.post(
            f"{BASE_URL}/actions/A-001/update",
            json={"status": "Closed", "description": "Done"},
        )
        assert r.status_code == 200
        action = r.get_json()["meeting"]["actions"][0]
        assert action["status"] == "Closed"

    def test_update_action_not_found_returns_404(self, mrc_crud_client):
        r = mrc_crud_client.post(
            f"{BASE_URL}/actions/A-999/update",
            json={"status": "Closed"},
        )
        assert r.status_code == 404

    def test_delete_action_returns_200(self, mrc_crud_client):
        r = mrc_crud_client.post(f"{BASE_URL}/actions/A-001/delete")
        assert r.status_code == 200
        assert len(r.get_json()["meeting"]["actions"]) == 0

    def test_delete_action_missing_meeting_returns_404(self, mrc_crud_client):
        r = mrc_crud_client.post(
            "/api/v1/governance/mrc/meetings/GHOST/actions/A-001/delete"
        )
        assert r.status_code == 404


# ===========================================================================
# Participants CRUD
# ===========================================================================

class TestParticipantsCrud:

    def test_add_participant_returns_200(self, mrc_crud_client):
        r = mrc_crud_client.post(
            f"{BASE_URL}/participants",
            json={"name": "Bob", "role": "CTO",
                  "organisation": "MKM", "status": "Invited"},
        )
        assert r.status_code == 200
        meeting = r.get_json()["meeting"]
        assert len(meeting["participants"]) == 2

    def test_add_participant_auto_id(self, mrc_crud_client):
        r = mrc_crud_client.post(f"{BASE_URL}/participants",
                                  json={"name": "Bob"})
        participants = r.get_json()["meeting"]["participants"]
        ids = [p["id"] for p in participants]
        assert "P-001" in ids
        assert "P-002" in ids

    def test_add_participant_missing_meeting_returns_404(self, mrc_crud_client):
        r = mrc_crud_client.post(
            "/api/v1/governance/mrc/meetings/GHOST/participants",
            json={"name": "x"},
        )
        assert r.status_code == 404

    def test_update_participant_returns_200(self, mrc_crud_client):
        r = mrc_crud_client.post(
            f"{BASE_URL}/participants/P-001/update",
            json={"status": "Confirmed", "role": "CFO"},
        )
        assert r.status_code == 200
        p = r.get_json()["meeting"]["participants"][0]
        assert p["role"] == "CFO"

    def test_update_participant_not_found_returns_404(self, mrc_crud_client):
        r = mrc_crud_client.post(
            f"{BASE_URL}/participants/P-999/update",
            json={"status": "x"},
        )
        assert r.status_code == 404

    def test_delete_participant_returns_200(self, mrc_crud_client):
        r = mrc_crud_client.post(f"{BASE_URL}/participants/P-001/delete")
        assert r.status_code == 200
        assert len(r.get_json()["meeting"]["participants"]) == 0

    def test_delete_participant_missing_meeting_returns_404(self, mrc_crud_client):
        r = mrc_crud_client.post(
            "/api/v1/governance/mrc/meetings/GHOST/participants/P-001/delete"
        )
        assert r.status_code == 404
