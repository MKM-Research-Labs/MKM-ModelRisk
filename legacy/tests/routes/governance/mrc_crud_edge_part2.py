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
Tests for MRC meeting CRUD — malformed IDs, missing meetings, string→list conversion (part 2).

Split from mrc_crud_edge.py.
"""

import copy
import json

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


def _make_crud_client(tmp_path, monkeypatch, meeting):
    """Create a Flask test client with the given meeting data."""
    import routes.governance._constants as gov_constants
    from config import config

    meetings_path = str(tmp_path / "mrc_meetings.json")
    inv_path = str(tmp_path / "model_inventory.json")
    audit_path = str(tmp_path / "model_audit_log.json")

    with open(meetings_path, "w") as f:
        json.dump([meeting], f)
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


@pytest.fixture
def mrc_crud_client(tmp_path, monkeypatch):
    """Flask test client with standard MRC meeting data."""
    return _make_crud_client(tmp_path, monkeypatch, copy.deepcopy(_BASE_MEETING))


BASE_URL = "/api/v1/governance/mrc/meetings/MRC-2026-001"


# ===========================================================================
# Malformed IDs
# ===========================================================================

class TestMalformedDecisionId:
    """Lines 129-130: existing decision with malformed ID triggers except."""

    @pytest.fixture
    def mrc_crud_malformed_decisions(self, tmp_path, monkeypatch):
        meeting = copy.deepcopy(_BASE_MEETING)
        meeting["decisions"].append({"id": "BADID", "description": "Malformed", "date": "2026-01-01"})
        return _make_crud_client(tmp_path, monkeypatch, meeting)

    def test_add_decision_with_malformed_existing_id(self, mrc_crud_malformed_decisions):
        r = mrc_crud_malformed_decisions.post(
            f"{BASE_URL}/decisions",
            json={"description": "New after malformed"},
        )
        assert r.status_code == 200
        decisions = r.get_json()["meeting"]["decisions"]
        ids = [d["id"] for d in decisions]
        assert "D-002" in ids


class TestMalformedActionId:
    """Lines 191-192: existing action with malformed ID triggers except."""

    @pytest.fixture
    def mrc_crud_malformed_actions(self, tmp_path, monkeypatch):
        meeting = copy.deepcopy(_BASE_MEETING)
        meeting["actions"].append({"id": "NOPE", "description": "Bad", "owner": "X",
                                   "target_date": "", "status": "Open"})
        return _make_crud_client(tmp_path, monkeypatch, meeting)

    def test_add_action_with_malformed_existing_id(self, mrc_crud_malformed_actions):
        r = mrc_crud_malformed_actions.post(
            f"{BASE_URL}/actions",
            json={"description": "New action"},
        )
        assert r.status_code == 200
        actions = r.get_json()["meeting"]["actions"]
        ids = [a["id"] for a in actions]
        assert "A-002" in ids


class TestMalformedParticipantId:
    """Lines 255-256: existing participant with malformed ID triggers except."""

    @pytest.fixture
    def mrc_crud_malformed_participants(self, tmp_path, monkeypatch):
        meeting = copy.deepcopy(_BASE_MEETING)
        meeting["participants"].append({"id": "WRONG", "name": "X", "role": "",
                                        "organisation": "", "status": "Invited"})
        return _make_crud_client(tmp_path, monkeypatch, meeting)

    def test_add_participant_with_malformed_existing_id(self, mrc_crud_malformed_participants):
        r = mrc_crud_malformed_participants.post(
            f"{BASE_URL}/participants",
            json={"name": "New Person"},
        )
        assert r.status_code == 200
        participants = r.get_json()["meeting"]["participants"]
        ids = [p["id"] for p in participants]
        assert "P-002" in ids


class TestUpdateMissingMeeting:
    """Lines 147, 211, 275, 333: update endpoints with missing meeting → 404."""

    def test_update_decision_missing_meeting_returns_404(self, mrc_crud_client):
        r = mrc_crud_client.post(
            "/api/v1/governance/mrc/meetings/GHOST/decisions/D-001/update",
            json={"description": "x"},
        )
        assert r.status_code == 404

    def test_update_action_missing_meeting_returns_404(self, mrc_crud_client):
        r = mrc_crud_client.post(
            "/api/v1/governance/mrc/meetings/GHOST/actions/A-001/update",
            json={"status": "Closed"},
        )
        assert r.status_code == 404

    def test_update_participant_missing_meeting_returns_404(self, mrc_crud_client):
        r = mrc_crud_client.post(
            "/api/v1/governance/mrc/meetings/GHOST/participants/P-001/update",
            json={"status": "Confirmed"},
        )
        assert r.status_code == 404

    def test_update_minute_item_missing_meeting_returns_404(self, mrc_crud_client):
        r = mrc_crud_client.post(
            "/api/v1/governance/mrc/meetings/GHOST/minutes-items/1/update",
            json={"text": "x"},
        )
        assert r.status_code == 404


class TestMinutesStringToListConversion:
    """Line 314: add_minute_item when minutes is a string (legacy) converts to empty list."""

    def test_add_minute_item_when_minutes_is_string(self, mrc_crud_client):
        mrc_crud_client.post(f"{BASE_URL}/minutes/update",
                             json={"minutes": "legacy text"})
        r = mrc_crud_client.post(
            f"{BASE_URL}/minutes-items",
            json={"title": "New Item", "text": "Some text", "presenter": "Chair"},
        )
        assert r.status_code == 200
        meeting = r.get_json()["meeting"]
        assert isinstance(meeting["minutes"], list)
        assert len(meeting["minutes"]) == 1
        assert meeting["minutes"][0]["title"] == "New Item"
