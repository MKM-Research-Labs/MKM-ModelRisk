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
Tests for MRC meeting CRUD — minutes items (part 1).

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
# Minutes Items CRUD
# ===========================================================================

class TestMinutesItemsCrud:

    def test_add_minute_item_returns_200(self, mrc_crud_client):
        r = mrc_crud_client.post(
            f"{BASE_URL}/minutes-items",
            json={"title": "AOB", "text": "No other business.",
                  "presenter": "Chair"},
        )
        assert r.status_code == 200
        meeting = r.get_json()["meeting"]
        assert isinstance(meeting["minutes"], list)
        assert len(meeting["minutes"]) == 2

    def test_add_minute_item_missing_meeting_returns_404(self, mrc_crud_client):
        r = mrc_crud_client.post(
            "/api/v1/governance/mrc/meetings/GHOST/minutes-items",
            json={"title": "x"},
        )
        assert r.status_code == 404

    def test_update_minute_item_returns_200(self, mrc_crud_client):
        r = mrc_crud_client.post(
            f"{BASE_URL}/minutes-items/1/update",
            json={"text": "Updated text."},
        )
        assert r.status_code == 200
        item = r.get_json()["meeting"]["minutes"][0]
        assert item["text"] == "Updated text."

    def test_update_minute_item_not_found_returns_404(self, mrc_crud_client):
        r = mrc_crud_client.post(
            f"{BASE_URL}/minutes-items/999/update",
            json={"text": "x"},
        )
        assert r.status_code == 404

    def test_update_minute_item_legacy_format_returns_400(self, mrc_crud_client):
        """When minutes is a string (legacy), updating an item returns 400."""
        mrc_crud_client.post(f"{BASE_URL}/minutes/update",
                             json={"minutes": "legacy text"})
        r = mrc_crud_client.post(
            f"{BASE_URL}/minutes-items/1/update",
            json={"text": "x"},
        )
        assert r.status_code == 400

    def test_delete_minute_item_returns_200(self, mrc_crud_client):
        # Add another item first
        mrc_crud_client.post(f"{BASE_URL}/minutes-items",
                             json={"title": "Extra"})
        r = mrc_crud_client.post(f"{BASE_URL}/minutes-items/1/delete")
        assert r.status_code == 200
        meeting = r.get_json()["meeting"]
        assert len(meeting["minutes"]) == 1
        assert meeting["minutes"][0]["item"] == 1  # Renumbered

    def test_delete_minute_item_legacy_format_returns_400(self, mrc_crud_client):
        """When minutes is a string, deleting returns 400."""
        mrc_crud_client.post(f"{BASE_URL}/minutes/update",
                             json={"minutes": "legacy text"})
        r = mrc_crud_client.post(f"{BASE_URL}/minutes-items/1/delete")
        assert r.status_code == 400

    def test_delete_minute_item_missing_meeting_returns_404(self, mrc_crud_client):
        r = mrc_crud_client.post(
            "/api/v1/governance/mrc/meetings/GHOST/minutes-items/1/delete"
        )
        assert r.status_code == 404
