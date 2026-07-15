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
"""Tests for meeting close-out: minutes generation, serving, and prior-minutes."""
from __future__ import annotations

from src.files import upload_path
from tests.web.conftest import HEADERS
from tests.web.test_mrc_signoff_api import _schedule_meeting, _seed_mrc


def _stub_pdf(monkeypatch):
    # Avoid a real tectonic run — the minutes PDF renders from a stubbed engine.
    monkeypatch.setattr(
        "src.governance.mrc.pack.compile_tex", lambda tex, assets=None: b"%PDF-close")


def _resolve_all_agenda(client, meeting_id="MTG1"):
    """Mark every seeded standing agenda item Completed so the meeting can close."""
    agenda = client.get(f"/api/meetings/{meeting_id}").get_json()["data"]["agenda"]
    for item in agenda:
        client.post(
            f"/api/meetings/{meeting_id}/collections/agenda/{item['item_id']}",
            json={"fields": {"status": "Completed"}, "confirmed": True}, headers=HEADERS,
        )


def _ready_to_close(client, monkeypatch, meeting_id="MTG1", date="2026-06-30"):
    _stub_pdf(monkeypatch)
    _seed_mrc(client)
    _schedule_meeting(client, meeting_id=meeting_id, date=date)
    _resolve_all_agenda(client, meeting_id)


def test_close_meeting_generates_minutes_and_completes(client, monkeypatch):
    _ready_to_close(client, monkeypatch)
    response = client.post("/api/meetings/MTG1/close", json={"confirmed": True}, headers=HEADERS)
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["status"] == "Completed"
    assert data["minutes_filename"]


def test_close_meeting_unknown_is_404(client):
    response = client.post("/api/meetings/none/close", json={"confirmed": True}, headers=HEADERS)
    assert response.status_code == 404


def test_close_meeting_requires_confirmation(client, monkeypatch):
    _ready_to_close(client, monkeypatch)
    # No confirmed flag → the close is gated before any PDF work happens.
    assert client.post("/api/meetings/MTG1/close", json={}, headers=HEADERS).status_code == 409


def test_close_meeting_blocked_while_agenda_open(client, monkeypatch):
    _stub_pdf(monkeypatch)
    _seed_mrc(client)
    _schedule_meeting(client)                     # seeded standing items left Pending
    response = client.post("/api/meetings/MTG1/close", json={"confirmed": True}, headers=HEADERS)
    assert response.status_code == 400
    assert "agenda items still open" in response.get_json()["error"]


def test_close_meeting_blocked_when_not_quorate(client):
    # A strict committee (default quorum) with no attendance is never quorate.
    client.post("/api/reference/collections/mrc",
                json={"fields": {"value": "MRC-STRICT", "name": "MRC-STRICT", "level": "Company"},
                      "confirmed": True}, headers=HEADERS)
    _schedule_meeting(client, mrc="MRC-STRICT")
    response = client.post("/api/meetings/MTG1/close", json={"confirmed": True}, headers=HEADERS)
    assert response.status_code == 400
    assert "quorate" in response.get_json()["error"]


def test_close_meeting_already_closed_is_400(client, monkeypatch):
    _ready_to_close(client, monkeypatch)
    client.post("/api/meetings/MTG1/close", json={"confirmed": True}, headers=HEADERS)
    again = client.post("/api/meetings/MTG1/close", json={"confirmed": True}, headers=HEADERS)
    assert again.status_code == 400
    assert "already closed" in again.get_json()["error"]


def test_minutes_pdf_served_after_close(client, monkeypatch):
    _ready_to_close(client, monkeypatch)
    client.post("/api/meetings/MTG1/close", json={"confirmed": True}, headers=HEADERS)
    response = client.get("/api/meetings/MTG1/minutes.pdf")
    assert response.status_code == 200
    assert response.mimetype == "application/pdf"
    assert response.data.startswith(b"%PDF")


def test_minutes_pdf_unknown_meeting_is_404(client):
    assert client.get("/api/meetings/none/minutes.pdf").status_code == 404


def test_minutes_pdf_before_close_is_404(client):
    _seed_mrc(client)
    _schedule_meeting(client)
    response = client.get("/api/meetings/MTG1/minutes.pdf")
    assert response.status_code == 404
    assert "not generated" in response.get_json()["error"]


def test_minutes_pdf_missing_file_is_404(client, monkeypatch):
    _ready_to_close(client, monkeypatch)
    client.post("/api/meetings/MTG1/close", json={"confirmed": True}, headers=HEADERS)
    filename = client.get("/api/meetings/MTG1").get_json()["data"]["minutes_filename"]
    upload_path("meeting_minutes", filename).unlink()   # delete the stored minutes
    response = client.get("/api/meetings/MTG1/minutes.pdf")
    assert response.status_code == 404
    assert "missing" in response.get_json()["error"]


def test_prior_minutes_lists_earlier_closed_meeting(client, monkeypatch):
    _ready_to_close(client, monkeypatch, meeting_id="MTG1", date="2026-03-01")
    client.post("/api/meetings/MTG1/close", json={"confirmed": True}, headers=HEADERS)
    _schedule_meeting(client, meeting_id="MTG2", date="2026-06-01")   # same committee, later
    prior = client.get("/api/meetings/MTG2/prior-minutes").get_json()
    assert [m["meeting_id"] for m in prior] == ["MTG1"]


def test_prior_minutes_excludes_self_and_later(client, monkeypatch):
    _ready_to_close(client, monkeypatch, meeting_id="MTG1", date="2026-06-01")
    client.post("/api/meetings/MTG1/close", json={"confirmed": True}, headers=HEADERS)
    # Querying MTG1 itself: it is neither earlier than itself nor a different meeting.
    assert client.get("/api/meetings/MTG1/prior-minutes").get_json() == []


def test_prior_minutes_unknown_meeting_is_404(client):
    assert client.get("/api/meetings/none/prior-minutes").status_code == 404


def test_prior_minutes_skips_later_dated_meeting(client, monkeypatch):
    _stub_pdf(monkeypatch)
    _seed_mrc(client)
    for meeting_id, when in (("MTG1", "2026-03-01"), ("MTG2", "2026-06-01")):
        _schedule_meeting(client, meeting_id=meeting_id, date=when)
        _resolve_all_agenda(client, meeting_id)
        client.post(f"/api/meetings/{meeting_id}/close", json={"confirmed": True}, headers=HEADERS)
    # Prior-minutes for the *earlier* meeting: the later MTG2 is excluded by date.
    assert client.get("/api/meetings/MTG1/prior-minutes").get_json() == []
