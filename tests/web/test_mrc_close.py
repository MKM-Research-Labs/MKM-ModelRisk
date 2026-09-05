# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
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

from config.governance import STANDING_AGENDA_LIST
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


def test_closed_meeting_refuses_every_amendment(client, monkeypatch):
    """Closing locks the meeting down. Its minutes are generated and filed, so
    editing it afterwards would change what the committee is recorded as having
    decided — renaming it, reopening it, moving its date, rewriting or deleting an
    agenda item, adding to it, or unlocking the agenda are all refused. A
    correction is raised and minuted at the next meeting instead."""
    _ready_to_close(client, monkeypatch)
    item_id = client.get("/api/meetings/MTG1").get_json()["data"]["agenda"][0]["item_id"]
    client.post("/api/meetings/MTG1/close", json={"confirmed": True}, headers=HEADERS)

    attempts = [
        ("/api/meetings/MTG1/field", {"field": "title", "value": "Renamed after the fact"}),
        ("/api/meetings/MTG1/field", {"field": "status", "value": "Scheduled"}),
        ("/api/meetings/MTG1/field", {"field": "date", "value": "2026-12-01"}),
        ("/api/meetings/MTG1/collections/actions", {"fields": {"description": "Late action"}}),
        (f"/api/meetings/MTG1/collections/agenda/{item_id}", {"fields": {"title": "Rewritten"}}),
        (f"/api/meetings/MTG1/collections/agenda/{item_id}/delete", {}),
        ("/api/meetings/MTG1/unlock-agenda", {}),
    ]
    for path, body in attempts:
        response = client.post(path, json={**body, "confirmed": True}, headers=HEADERS)
        assert response.status_code == 400, path
        assert "closed" in response.get_json()["error"], path


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


def test_a_committee_with_no_minutes_item_still_closes(client, monkeypatch):
    """The successor is scheduled from the institution's own standing agenda. One
    that carries no previous-minutes item simply has nowhere to table the paper —
    which must cost the successor its tabled minutes, never the close."""
    _stub_pdf(monkeypatch)
    _seed_mrc(client)
    client.post(f"/api/reference/collections/{STANDING_AGENDA_LIST}",
                json={"fields": {"title": "Attendance", "kind": "rollcall"},
                      "confirmed": True}, headers=HEADERS)
    _schedule_meeting(client, meeting_id="MTG-NM-Q3", date="2026-06-30")
    _resolve_all_agenda(client, "MTG-NM-Q3")
    assert client.post("/api/meetings/MTG-NM-Q3/close", json={"confirmed": True},
                       headers=HEADERS).status_code == 200

    successor = [m for m in client.get("/api/meetings").get_json()
                 if m["meeting_id"] != "MTG-NM-Q3"]
    assert successor, "the next meeting is still scheduled"
    agenda = client.get(
        f"/api/meetings/{successor[0]['meeting_id']}").get_json()["data"]["agenda"]
    assert [i["title"] for i in agenda] == ["Attendance"]


def test_a_meeting_with_no_date_gets_no_successor(client, monkeypatch):
    """Best-effort: the close is already recorded, so a meeting that cannot say
    when the next one falls simply gets none rather than a failed close."""
    _ready_to_close(client, monkeypatch, meeting_id="MTG-ND", date="2026-06-30")
    blanked = client.post("/api/meetings/MTG-ND/field",
                          json={"field": "date", "value": "", "confirmed": True},
                          headers=HEADERS)
    assert blanked.status_code == 200, blanked.get_json()
    assert client.post("/api/meetings/MTG-ND/close", json={"confirmed": True},
                       headers=HEADERS).status_code == 200
    assert [m["meeting_id"] for m in client.get("/api/meetings").get_json()] \
        == ["MTG-ND"]
