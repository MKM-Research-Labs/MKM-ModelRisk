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

"""Tests for MRC meeting CRUD — list, create, get, update, documents."""

import io

import pytest

from tests.routes.governance.conftest import create_meeting


# ===========================================================================
# GET /governance/mrc/meetings  —  list
# ===========================================================================

class TestListMeetings:

    def test_empty_list_returns_success(self, mrc_client):
        r = mrc_client.get("/api/v1/governance/mrc/meetings")
        assert r.status_code == 200
        data = r.get_json()
        assert data["status"] == "success"
        assert data["meetings"] == []

    def test_created_meeting_appears_in_list(self, mrc_client):
        create_meeting(mrc_client, title="Board Meeting")
        r = mrc_client.get("/api/v1/governance/mrc/meetings")
        data = r.get_json()
        assert len(data["meetings"]) == 1
        assert data["meetings"][0]["title"] == "Board Meeting"

    def test_list_summary_has_required_keys(self, mrc_client):
        create_meeting(mrc_client)
        r = mrc_client.get("/api/v1/governance/mrc/meetings")
        m = r.get_json()["meetings"][0]
        for key in ("id", "title", "date", "status", "chair",
                    "agenda_items", "has_minutes", "documents"):
            assert key in m, f"Missing key: {key}"

    def test_sorted_by_date_desc(self, mrc_client):
        create_meeting(mrc_client, date="2025-01-01")
        create_meeting(mrc_client, date="2026-06-01")
        r = mrc_client.get("/api/v1/governance/mrc/meetings")
        dates = [m["date"] for m in r.get_json()["meetings"]]
        assert dates == sorted(dates, reverse=True)


# ===========================================================================
# POST /governance/mrc/meetings  —  create
# ===========================================================================

class TestCreateMeeting:

    def test_create_returns_meeting(self, mrc_client):
        r, data = create_meeting(mrc_client)
        assert r.status_code == 200
        assert data["status"] == "success"
        assert "meeting" in data

    def test_default_chair_populated(self, mrc_client):
        _, data = create_meeting(mrc_client)
        assert data["meeting"]["chair"] == "Johnny Mattimore"

    def test_custom_title_used(self, mrc_client):
        _, data = create_meeting(mrc_client, title="Quarterly Review")
        assert data["meeting"]["title"] == "Quarterly Review"

    def test_auto_generates_id(self, mrc_client):
        _, data = create_meeting(mrc_client)
        assert "id" in data["meeting"]
        assert len(data["meeting"]["id"]) > 0

    def test_default_participants_created(self, mrc_client):
        _, data = create_meeting(mrc_client)
        participants = data["meeting"]["participants"]
        assert len(participants) >= 1

    def test_custom_attendees_become_participants(self, mrc_client):
        attendees = [{"name": "Alice Smith", "role": "CRO"}]
        _, data = create_meeting(mrc_client, attendees=attendees)
        names = [p["name"] for p in data["meeting"]["participants"]]
        assert "Alice Smith" in names

    def test_no_json_body_uses_defaults(self, mrc_client):
        r = mrc_client.post("/api/v1/governance/mrc/meetings")
        assert r.status_code == 200
        assert r.get_json()["status"] == "success"


# ===========================================================================
# GET /governance/mrc/meetings/<id>  —  get single
# ===========================================================================

class TestGetMeeting:

    def test_get_created_meeting(self, mrc_client):
        _, created = create_meeting(mrc_client)
        mid = created["meeting"]["id"]
        r = mrc_client.get(f"/api/v1/governance/mrc/meetings/{mid}")
        assert r.status_code == 200
        data = r.get_json()
        assert data["status"] == "success"
        assert data["meeting"]["id"] == mid

    def test_unknown_id_returns_404(self, mrc_client):
        r = mrc_client.get("/api/v1/governance/mrc/meetings/nonexistent")
        assert r.status_code == 404
        assert r.get_json()["status"] == "error"


# ===========================================================================
# POST /governance/mrc/meetings/<id>/update  —  update
# ===========================================================================

class TestUpdateMeeting:

    def test_update_title(self, mrc_client):
        _, created = create_meeting(mrc_client)
        mid = created["meeting"]["id"]
        r = mrc_client.post(
            f"/api/v1/governance/mrc/meetings/{mid}/update",
            json={"title": "Updated Title"},
        )
        assert r.status_code == 200
        assert r.get_json()["meeting"]["title"] == "Updated Title"

    def test_update_unknown_id_returns_404(self, mrc_client):
        r = mrc_client.post(
            "/api/v1/governance/mrc/meetings/bad-id/update",
            json={"title": "X"},
        )
        assert r.status_code == 404

    def test_update_sets_updated_at(self, mrc_client):
        _, created = create_meeting(mrc_client)
        mid = created["meeting"]["id"]
        r = mrc_client.post(
            f"/api/v1/governance/mrc/meetings/{mid}/update",
            json={"status": "Completed"},
        )
        assert r.get_json()["meeting"]["updated_at"] is not None


# ===========================================================================
# Document upload / serve
# ===========================================================================

class TestMeetingDocuments:

    def test_upload_not_found_meeting_returns_404(self, mrc_client):
        r = mrc_client.post(
            "/api/v1/governance/mrc/meetings/ghost/documents",
            data={},
        )
        assert r.status_code == 404

    def test_upload_no_file_returns_400(self, mrc_client):
        _, created = create_meeting(mrc_client)
        mid = created["meeting"]["id"]
        r = mrc_client.post(
            f"/api/v1/governance/mrc/meetings/{mid}/documents",
            data={},
        )
        assert r.status_code == 400
        assert r.get_json()["status"] == "error"

    def test_upload_empty_filename_returns_400(self, mrc_client):
        _, created = create_meeting(mrc_client)
        mid = created["meeting"]["id"]
        r = mrc_client.post(
            f"/api/v1/governance/mrc/meetings/{mid}/documents",
            data={"file": (io.BytesIO(b""), "")},
            content_type="multipart/form-data",
        )
        assert r.status_code == 400

    def test_serve_missing_document_returns_404(self, mrc_client):
        _, created = create_meeting(mrc_client)
        mid = created["meeting"]["id"]
        r = mrc_client.get(
            f"/api/v1/governance/mrc/meetings/{mid}/documents/notafile.pdf"
        )
        assert r.status_code == 404
