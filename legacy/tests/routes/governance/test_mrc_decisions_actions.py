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

"""Tests for MRC decisions, actions, and participants CRUD."""

import pytest

from tests.routes.governance.conftest import create_meeting


# ===========================================================================
# Decisions CRUD
# ===========================================================================

class TestDecisionsCRUD:

    @pytest.fixture(autouse=True)
    def setup(self, mrc_client):
        self.client = mrc_client
        _, created = create_meeting(mrc_client)
        self.mid = created["meeting"]["id"]

    def _add_decision(self, description="Approve model"):
        return self.client.post(
            f"/api/v1/governance/mrc/meetings/{self.mid}/decisions",
            json={"description": description},
        )

    def test_add_decision_auto_generates_id(self):
        r = self._add_decision()
        assert r.status_code == 200
        decisions = r.get_json()["meeting"]["decisions"]
        assert decisions[0]["id"] == "D-001"

    def test_second_decision_increments_id(self):
        self._add_decision("First")
        r = self._add_decision("Second")
        ids = [d["id"] for d in r.get_json()["meeting"]["decisions"]]
        assert ids == ["D-001", "D-002"]

    def test_add_decision_unknown_meeting_returns_404(self):
        r = self.client.post(
            "/api/v1/governance/mrc/meetings/ghost/decisions",
            json={"description": "X"},
        )
        assert r.status_code == 404

    def test_update_decision(self):
        self._add_decision()
        r = self.client.post(
            f"/api/v1/governance/mrc/meetings/{self.mid}/decisions/D-001/update",
            json={"description": "Updated decision"},
        )
        assert r.status_code == 200
        assert r.get_json()["meeting"]["decisions"][0]["description"] == "Updated decision"

    def test_update_missing_decision_returns_404(self):
        r = self.client.post(
            f"/api/v1/governance/mrc/meetings/{self.mid}/decisions/D-999/update",
            json={"description": "X"},
        )
        assert r.status_code == 404

    def test_delete_decision(self):
        self._add_decision()
        self._add_decision("Second")
        r = self.client.post(
            f"/api/v1/governance/mrc/meetings/{self.mid}/decisions/D-001/delete"
        )
        assert r.status_code == 200
        assert len(r.get_json()["meeting"]["decisions"]) == 1

    def test_delete_decision_unknown_meeting_returns_404(self):
        r = self.client.post(
            "/api/v1/governance/mrc/meetings/ghost/decisions/D-001/delete"
        )
        assert r.status_code == 404


# ===========================================================================
# Actions CRUD
# ===========================================================================

class TestActionsCRUD:

    @pytest.fixture(autouse=True)
    def setup(self, mrc_client):
        self.client = mrc_client
        _, created = create_meeting(mrc_client)
        self.mid = created["meeting"]["id"]

    def _add_action(self, description="Review model"):
        return self.client.post(
            f"/api/v1/governance/mrc/meetings/{self.mid}/actions",
            json={"description": description, "owner": "Alice", "status": "Open"},
        )

    def test_add_action_auto_generates_id(self):
        r = self._add_action()
        assert r.status_code == 200
        actions = r.get_json()["meeting"]["actions"]
        assert actions[0]["id"] == "A-001"
        assert actions[0]["status"] == "Open"

    def test_add_action_unknown_meeting_returns_404(self):
        r = self.client.post(
            "/api/v1/governance/mrc/meetings/ghost/actions",
            json={"description": "X"},
        )
        assert r.status_code == 404

    def test_update_action_status(self):
        self._add_action()
        r = self.client.post(
            f"/api/v1/governance/mrc/meetings/{self.mid}/actions/A-001/update",
            json={"status": "Closed"},
        )
        assert r.status_code == 200
        assert r.get_json()["meeting"]["actions"][0]["status"] == "Closed"

    def test_update_missing_action_returns_404(self):
        r = self.client.post(
            f"/api/v1/governance/mrc/meetings/{self.mid}/actions/A-999/update",
            json={"status": "Closed"},
        )
        assert r.status_code == 404

    def test_delete_action(self):
        self._add_action()
        r = self.client.post(
            f"/api/v1/governance/mrc/meetings/{self.mid}/actions/A-001/delete"
        )
        assert r.status_code == 200
        assert r.get_json()["meeting"]["actions"] == []

    def test_delete_action_unknown_meeting_returns_404(self):
        r = self.client.post(
            "/api/v1/governance/mrc/meetings/ghost/actions/A-001/delete"
        )
        assert r.status_code == 404


# ===========================================================================
# Participants CRUD
# ===========================================================================

class TestParticipantsCRUD:

    @pytest.fixture(autouse=True)
    def setup(self, mrc_client):
        self.client = mrc_client
        _, created = create_meeting(mrc_client, attendees=[])
        self.mid = created["meeting"]["id"]
        # Clear auto-generated participants by setting empty
        self.client.post(
            f"/api/v1/governance/mrc/meetings/{self.mid}/update",
            json={"participants": []},
        )

    def _add_participant(self, name="Bob Brown"):
        return self.client.post(
            f"/api/v1/governance/mrc/meetings/{self.mid}/participants",
            json={"name": name, "role": "Observer", "organisation": "FCA"},
        )

    def test_add_participant_auto_generates_id(self):
        r = self._add_participant()
        assert r.status_code == 200
        participants = r.get_json()["meeting"]["participants"]
        # Find our new participant (may have existing ones from auto-generation)
        new_p = next(p for p in participants if p["name"] == "Bob Brown")
        assert new_p["id"].startswith("P-")

    def test_add_participant_unknown_meeting_returns_404(self):
        r = self.client.post(
            "/api/v1/governance/mrc/meetings/ghost/participants",
            json={"name": "X"},
        )
        assert r.status_code == 404

    def test_update_participant(self):
        self._add_participant()
        r = self.client.get(f"/api/v1/governance/mrc/meetings/{self.mid}")
        participants = r.get_json()["meeting"]["participants"]
        pid = next(p["id"] for p in participants if p["name"] == "Bob Brown")
        r = self.client.post(
            f"/api/v1/governance/mrc/meetings/{self.mid}/participants/{pid}/update",
            json={"status": "Attended"},
        )
        assert r.status_code == 200
        updated = next(
            p for p in r.get_json()["meeting"]["participants"] if p["id"] == pid
        )
        assert updated["status"] == "Attended"

    def test_update_missing_participant_returns_404(self):
        r = self.client.post(
            f"/api/v1/governance/mrc/meetings/{self.mid}/participants/P-999/update",
            json={"status": "Attended"},
        )
        assert r.status_code == 404

    def test_delete_participant(self):
        self._add_participant("Delete Me")
        r = self.client.get(f"/api/v1/governance/mrc/meetings/{self.mid}")
        participants = r.get_json()["meeting"]["participants"]
        pid = next(p["id"] for p in participants if p["name"] == "Delete Me")
        r = self.client.post(
            f"/api/v1/governance/mrc/meetings/{self.mid}/participants/{pid}/delete"
        )
        assert r.status_code == 200
        remaining = [p["id"] for p in r.get_json()["meeting"]["participants"]]
        assert pid not in remaining

    def test_delete_participant_unknown_meeting_returns_404(self):
        r = self.client.post(
            "/api/v1/governance/mrc/meetings/ghost/participants/P-001/delete"
        )
        assert r.status_code == 404
