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

"""Tests for MRC agenda items and minutes CRUD."""

import pytest

from tests.routes.governance.conftest import create_meeting


# ===========================================================================
# Agenda CRUD
# ===========================================================================

class TestAgendaCRUD:

    @pytest.fixture(autouse=True)
    def setup(self, mrc_client):
        self.client = mrc_client
        _, created = create_meeting(mrc_client)
        self.mid = created["meeting"]["id"]

    def test_add_agenda_item(self):
        r = self.client.post(
            f"/api/v1/governance/mrc/meetings/{self.mid}/agenda",
            json={"title": "Model Review", "presenter": "Alice"},
        )
        assert r.status_code == 200
        agenda = r.get_json()["meeting"]["agenda"]
        assert len(agenda) == 1
        assert agenda[0]["title"] == "Model Review"
        assert agenda[0]["item"] == 1

    def test_add_multiple_items_increments_number(self):
        for title in ("Item A", "Item B", "Item C"):
            self.client.post(
                f"/api/v1/governance/mrc/meetings/{self.mid}/agenda",
                json={"title": title},
            )
        r = self.client.get(f"/api/v1/governance/mrc/meetings/{self.mid}")
        agenda = r.get_json()["meeting"]["agenda"]
        assert [a["item"] for a in agenda] == [1, 2, 3]

    def test_add_agenda_unknown_meeting_returns_404(self):
        r = self.client.post(
            "/api/v1/governance/mrc/meetings/ghost/agenda",
            json={"title": "X"},
        )
        assert r.status_code == 404

    def test_update_agenda_item(self):
        self.client.post(
            f"/api/v1/governance/mrc/meetings/{self.mid}/agenda",
            json={"title": "Original"},
        )
        r = self.client.post(
            f"/api/v1/governance/mrc/meetings/{self.mid}/agenda/1/update",
            json={"title": "Updated", "status": "Discussed"},
        )
        assert r.status_code == 200
        item = r.get_json()["meeting"]["agenda"][0]
        assert item["title"] == "Updated"
        assert item["status"] == "Discussed"

    def test_update_missing_item_returns_404(self):
        r = self.client.post(
            f"/api/v1/governance/mrc/meetings/{self.mid}/agenda/99/update",
            json={"title": "X"},
        )
        assert r.status_code == 404

    def test_update_agenda_unknown_meeting_returns_404(self):
        r = self.client.post(
            "/api/v1/governance/mrc/meetings/ghost/agenda/1/update",
            json={"title": "X"},
        )
        assert r.status_code == 404

    def test_delete_agenda_item_renumbers(self):
        for t in ("A", "B", "C"):
            self.client.post(
                f"/api/v1/governance/mrc/meetings/{self.mid}/agenda",
                json={"title": t},
            )
        self.client.post(
            f"/api/v1/governance/mrc/meetings/{self.mid}/agenda/2/delete",
        )
        r = self.client.get(f"/api/v1/governance/mrc/meetings/{self.mid}")
        agenda = r.get_json()["meeting"]["agenda"]
        assert len(agenda) == 2
        assert [a["item"] for a in agenda] == [1, 2]
        assert [a["title"] for a in agenda] == ["A", "C"]

    def test_delete_agenda_unknown_meeting_returns_404(self):
        r = self.client.post(
            "/api/v1/governance/mrc/meetings/ghost/agenda/1/delete"
        )
        assert r.status_code == 404


# ===========================================================================
# Minutes CRUD
# ===========================================================================

class TestMinutesCRUD:

    @pytest.fixture(autouse=True)
    def setup(self, mrc_client):
        self.client = mrc_client
        _, created = create_meeting(mrc_client)
        self.mid = created["meeting"]["id"]

    def test_update_minutes_text(self):
        r = self.client.post(
            f"/api/v1/governance/mrc/meetings/{self.mid}/minutes/update",
            json={"minutes": "# Minutes\n\nAll agreed."},
        )
        assert r.status_code == 200
        assert r.get_json()["meeting"]["minutes"] == "# Minutes\n\nAll agreed."

    def test_update_minutes_unknown_meeting_returns_404(self):
        r = self.client.post(
            "/api/v1/governance/mrc/meetings/ghost/minutes/update",
            json={"minutes": "text"},
        )
        assert r.status_code == 404

    def test_add_minute_item(self):
        r = self.client.post(
            f"/api/v1/governance/mrc/meetings/{self.mid}/minutes-items",
            json={"title": "Opening", "text": "Meeting called to order."},
        )
        assert r.status_code == 200
        minutes = r.get_json()["meeting"]["minutes"]
        assert isinstance(minutes, list)
        assert minutes[0]["title"] == "Opening"

    def test_update_minute_item_legacy_format_returns_400(self):
        # Set minutes to a string (legacy), then try to update an item
        self.client.post(
            f"/api/v1/governance/mrc/meetings/{self.mid}/minutes/update",
            json={"minutes": "legacy text"},
        )
        r = self.client.post(
            f"/api/v1/governance/mrc/meetings/{self.mid}/minutes-items/1/update",
            json={"title": "X"},
        )
        assert r.status_code == 400

    def test_update_minute_item_not_found_returns_404(self):
        # Add a list-format minute first
        self.client.post(
            f"/api/v1/governance/mrc/meetings/{self.mid}/minutes-items",
            json={"title": "Opening"},
        )
        r = self.client.post(
            f"/api/v1/governance/mrc/meetings/{self.mid}/minutes-items/99/update",
            json={"title": "X"},
        )
        assert r.status_code == 404

    def test_delete_minute_item_legacy_format_returns_400(self):
        self.client.post(
            f"/api/v1/governance/mrc/meetings/{self.mid}/minutes/update",
            json={"minutes": "legacy"},
        )
        r = self.client.post(
            f"/api/v1/governance/mrc/meetings/{self.mid}/minutes-items/1/delete"
        )
        assert r.status_code == 400
