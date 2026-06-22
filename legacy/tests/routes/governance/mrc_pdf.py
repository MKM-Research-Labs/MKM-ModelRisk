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
Tests for routes.governance.mrc_pdf — MRC meeting pack PDF generation.

Covers: _build_meeting_pdf (minimal meeting, all sections populated),
get_meeting_pdf route (meeting not found→404, valid meeting→200 PDF served).
"""

import copy
import json
from pathlib import Path

import pytest


_BASE_MEETING = {
    "id": "MRC-2026-001",
    "title": "MRC Q1 2026 Meeting",
    "date": "2026-03-15",
    "time": "10:00",
    "location": "Board Room",
    "status": "Confirmed",
    "chair": "CRO",
    "participants": [
        {"name": "Alice Smith", "role": "CRO", "organisation": "MKM", "status": "Confirmed"},
        {"name": "Bob Jones", "role": "Head of Quant", "organisation": "MKM", "status": "Confirmed"},
    ],
    "agenda": [
        {"item": 1, "title": "Minutes of previous meeting", "presenter": "Secretary", "status": "Standing"},
        {"item": 2, "title": "Model performance review", "presenter": "Head of Quant", "status": "Presentation"},
    ],
    "minutes": [
        {"item": 1, "title": "Minutes approved", "presenter": "Chair",
         "text": "Minutes of the previous meeting were reviewed and approved."},
    ],
    "decisions": [
        {"id": "D-001", "description": "Approve GEV model annual recertification", "date": "2026-03-15"},
    ],
    "actions": [
        {"id": "A-001", "description": "Update model documentation", "owner": "Head of Quant",
         "target_date": "2026-04-15", "status": "Open"},
    ],
}


# ===========================================================================
# _build_meeting_pdf (unit tests, no Flask needed)
# ===========================================================================

class TestBuildMeetingPdf:

    def test_returns_bytesio(self):
        from routes.governance.mrc_pdf import _build_meeting_pdf
        import io
        result = _build_meeting_pdf(_BASE_MEETING)
        assert isinstance(result, io.BytesIO)

    def test_buffer_not_empty(self):
        from routes.governance.mrc_pdf import _build_meeting_pdf
        result = _build_meeting_pdf(_BASE_MEETING)
        content = result.read()
        assert len(content) > 100  # non-trivial PDF

    def test_minimal_meeting(self):
        from routes.governance.mrc_pdf import _build_meeting_pdf
        import io
        result = _build_meeting_pdf({"id": "MIN-001", "title": "Minimal"})
        assert isinstance(result, io.BytesIO)

    def test_meeting_with_participants(self):
        from routes.governance.mrc_pdf import _build_meeting_pdf
        import io
        meeting = copy.deepcopy(_BASE_MEETING)
        result = _build_meeting_pdf(meeting)
        assert isinstance(result, io.BytesIO)

    def test_meeting_with_agenda(self):
        from routes.governance.mrc_pdf import _build_meeting_pdf
        import io
        meeting = {"title": "T", "agenda": [
            {"item": 1, "title": "Topic A", "presenter": "P1", "status": "Open"}
        ]}
        result = _build_meeting_pdf(meeting)
        assert isinstance(result, io.BytesIO)

    def test_meeting_with_minutes(self):
        from routes.governance.mrc_pdf import _build_meeting_pdf
        import io
        meeting = {"title": "T", "minutes": [
            {"item": 1, "title": "Minutes", "presenter": "Chair",
             "text": "Some\nnewline text"}
        ]}
        result = _build_meeting_pdf(meeting)
        assert isinstance(result, io.BytesIO)

    def test_meeting_with_decisions(self):
        from routes.governance.mrc_pdf import _build_meeting_pdf
        import io
        meeting = {"title": "T", "decisions": [
            {"id": "D-001", "description": "Decision text", "date": "2026-01-01"}
        ]}
        result = _build_meeting_pdf(meeting)
        assert isinstance(result, io.BytesIO)

    def test_meeting_with_actions(self):
        from routes.governance.mrc_pdf import _build_meeting_pdf
        import io
        meeting = {"title": "T", "actions": [
            {"id": "A-001", "description": "Do something", "owner": "P1",
             "target_date": "2026-04-01", "status": "Open"}
        ]}
        result = _build_meeting_pdf(meeting)
        assert isinstance(result, io.BytesIO)

    def test_all_sections(self):
        from routes.governance.mrc_pdf import _build_meeting_pdf
        import io
        result = _build_meeting_pdf(_BASE_MEETING)
        content = result.read()
        assert len(content) > 1000

    def test_meeting_with_no_optional_fields(self):
        """Meeting with no date/time/location/chair still works."""
        from routes.governance.mrc_pdf import _build_meeting_pdf
        import io
        result = _build_meeting_pdf({"title": "Bare minimum"})
        assert isinstance(result, io.BytesIO)


# ===========================================================================
# GET /governance/mrc/meetings/<meeting_id>/pdf
# ===========================================================================

@pytest.fixture
def mrc_pdf_client(tmp_path, monkeypatch):
    """Flask test client with an MRC meetings JSON file."""
    import routes.governance._constants as gov_constants
    from config import config

    meetings_path = str(tmp_path / "mrc_meetings.json")
    with open(meetings_path, "w") as f:
        json.dump([copy.deepcopy(_BASE_MEETING)], f)

    monkeypatch.setattr(gov_constants, "MRC_MEETINGS_PATH", meetings_path)
    monkeypatch.setattr(gov_constants, "INVENTORY_PATH", str(tmp_path / "inv.json"))
    monkeypatch.setattr(gov_constants, "AUDIT_LOG_PATH", str(tmp_path / "audit.json"))
    monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)

    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


@pytest.fixture
def mrc_pdf_no_meetings(tmp_path, monkeypatch):
    """Flask test client with empty meetings list."""
    import routes.governance._constants as gov_constants
    from config import config

    meetings_path = str(tmp_path / "mrc_meetings.json")
    with open(meetings_path, "w") as f:
        json.dump([], f)

    monkeypatch.setattr(gov_constants, "MRC_MEETINGS_PATH", meetings_path)
    monkeypatch.setattr(gov_constants, "INVENTORY_PATH", str(tmp_path / "inv.json"))
    monkeypatch.setattr(gov_constants, "AUDIT_LOG_PATH", str(tmp_path / "audit.json"))
    monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)

    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


class TestGetMeetingPdf:

    def test_meeting_not_found_returns_404(self, mrc_pdf_no_meetings):
        r = mrc_pdf_no_meetings.get("/api/v1/governance/mrc/meetings/MRC-GHOST/pdf")
        assert r.status_code == 404
        assert r.get_json()["status"] == "error"

    def test_valid_meeting_returns_pdf(self, mrc_pdf_client):
        r = mrc_pdf_client.get("/api/v1/governance/mrc/meetings/MRC-2026-001/pdf")
        assert r.status_code == 200

    def test_valid_meeting_content_type_pdf(self, mrc_pdf_client):
        r = mrc_pdf_client.get("/api/v1/governance/mrc/meetings/MRC-2026-001/pdf")
        if r.status_code == 200:
            assert "application/pdf" in r.content_type

    def test_valid_meeting_returns_bytes(self, mrc_pdf_client):
        r = mrc_pdf_client.get("/api/v1/governance/mrc/meetings/MRC-2026-001/pdf")
        if r.status_code == 200:
            assert len(r.data) > 100
