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
"""The closure loop for an agreed action: the owner asks, the committee grants.

The rule these cover is that nobody settles their own obligation — an owner records
progress and requests closure, and only the committee's ratification writes the closed
status.
"""
from __future__ import annotations

import io

from config.governance import ACTION_EVIDENCE_SCOPE
from src.files import upload_path
from tests.web._signoff_flows import _add, _schedule, _seed_mrc
from tests.web.conftest import HEADERS

REQUESTED = "Closure requested"


def _meeting_with_action(client, status="Open"):
    _seed_mrc(client)
    _schedule(client)
    added = _add(client, "actions", {"description": "Re-run the backtest", "status": status})
    return added.get_json()["data"]["actions"][0]["item_id"]


def _update(client, item_id, note="", status=None, file=None):
    data = {"note": note}
    if status:
        data["status"] = status
    if file is not None:
        data["file"] = file
    return client.post(
        f"/api/meetings/MTG1/collections/actions/{item_id}/updates",
        data=data, content_type="multipart/form-data", headers=HEADERS,
    )


def _ratify(client, item_id, meeting_id="MTG1", **body):
    return client.post(
        f"/api/meetings/{meeting_id}/action-closures/ratify",
        json={"item_id": item_id, "confirmed": True, **body}, headers=HEADERS,
    )


def _reject(client, item_id, meeting_id="MTG1", **body):
    return client.post(
        f"/api/meetings/{meeting_id}/action-closures/reject",
        json={"item_id": item_id, "confirmed": True, **body}, headers=HEADERS,
    )


def _close(client, monkeypatch, meeting_id="MTG1"):
    """Seal a meeting: resolve its seeded agenda, then close it on a stubbed PDF
    engine (a real tectonic run proves nothing about the closure rules)."""
    monkeypatch.setattr(
        "src.governance.mrc.pack.compile_tex", lambda tex, assets=None: b"%PDF-close")
    agenda = client.get(f"/api/meetings/{meeting_id}").get_json()["data"]["agenda"]
    for item in agenda:
        client.post(
            f"/api/meetings/{meeting_id}/collections/agenda/{item['item_id']}",
            json={"fields": {"status": "Completed"}, "confirmed": True}, headers=HEADERS,
        )
    closed = client.post(f"/api/meetings/{meeting_id}/close",
                         json={"confirmed": True}, headers=HEADERS)
    assert closed.status_code == 200, closed.get_json()


def test_an_owner_cannot_close_their_own_action(client):
    item_id = _meeting_with_action(client)
    refused = client.post(
        f"/api/meetings/MTG1/collections/actions/{item_id}",
        json={"fields": {"status": "Closed"}, "confirmed": True}, headers=HEADERS,
    )
    assert refused.status_code == 400
    assert REQUESTED in refused.get_json()["error"]


def test_an_action_cannot_be_agreed_already_closed(client):
    """Otherwise the add form is a way round the ratification the update path enforces."""
    _seed_mrc(client)
    _schedule(client)
    refused = _add(client, "actions", {"description": "Done already", "status": "Closed"})
    assert refused.status_code == 400
    assert REQUESTED in refused.get_json()["error"]


def test_owner_requests_closure_and_the_committee_ratifies_it(client):
    item_id = _meeting_with_action(client)
    requested = _update(client, item_id, note="Backtest complete", status=REQUESTED)
    assert requested.status_code == 201
    action = requested.get_json()["data"]["actions"][0]
    assert action["status"] == REQUESTED
    assert [u["note"] for u in action["updates"]] == ["Backtest complete"]

    ratified = _ratify(client, item_id, comments="Evidence reviewed and accepted.")
    assert ratified.status_code == 200
    data = ratified.get_json()["data"]
    assert data["actions"][0]["status"] == "Closed"
    # The closure is minuted, so the register shows the committee took the decision.
    assert any(item_id in (m.get("title") or "") for m in data["minutes"])


def test_ratifying_needs_a_requested_closure(client):
    """A committee cannot close an action nobody has said is done."""
    item_id = _meeting_with_action(client)
    refused = _ratify(client, item_id)
    assert refused.status_code == 400
    assert "closure has not been requested" in refused.get_json()["error"]


def test_ratifying_needs_confirmation(client):
    item_id = _meeting_with_action(client)
    _update(client, item_id, note="Done", status=REQUESTED)
    unconfirmed = client.post(
        "/api/meetings/MTG1/action-closures/ratify",
        json={"item_id": item_id}, headers=HEADERS,
    )
    assert unconfirmed.status_code == 409


def test_an_update_may_carry_supporting_evidence(client):
    item_id = _meeting_with_action(client)
    stored = _update(client, item_id, note="Backtest output",
                     file=(io.BytesIO(b"%PDF-1.4 backtest"), "backtest.pdf"))
    assert stored.status_code == 201
    update = stored.get_json()["data"]["actions"][0]["updates"][0]
    assert update["original_name"] == "backtest.pdf"

    downloaded = client.get(
        f"/api/meetings/MTG1/collections/actions/{item_id}/evidence/{update['filename']}",
        headers=HEADERS,
    )
    assert downloaded.status_code == 200
    assert downloaded.data == b"%PDF-1.4 backtest"


def test_evidence_is_only_reachable_through_its_own_action(client):
    item_id = _meeting_with_action(client)
    _update(client, item_id, note="Backtest output",
            file=(io.BytesIO(b"%PDF-1.4 backtest"), "backtest.pdf"))
    missing = client.get(
        f"/api/meetings/MTG1/collections/actions/{item_id}/evidence/somebody-elses.pdf",
        headers=HEADERS,
    )
    assert missing.status_code == 404


def test_an_action_outlives_the_meeting_that_agreed_it(client, monkeypatch):
    """The point of reviewing outstanding actions is that they were agreed earlier.

    A sealed meeting still holds what it decided — the wording, the owners — but the
    action's own status and history stay live, or a committee could never close what a
    previous meeting agreed.
    """
    item_id = _meeting_with_action(client)
    _schedule(client, meeting_id="MTG2", date="2026-09-30")
    _close(client, monkeypatch, "MTG1")

    # Sealed: the committee's record of what it agreed cannot be rewritten.
    reworded = client.post(
        f"/api/meetings/MTG1/collections/actions/{item_id}",
        json={"fields": {"description": "Something else"}, "confirmed": True}, headers=HEADERS,
    )
    assert reworded.status_code == 400
    assert "closed" in reworded.get_json()["error"]

    # Live: progress and closure still run, and the closure is minuted at MTG2 — the
    # meeting that actually took the decision.
    assert _update(client, item_id, note="Done", status=REQUESTED).status_code == 201
    ratified = _ratify(client, item_id, meeting_id="MTG2", source_meeting_id="MTG1")
    assert ratified.status_code == 200
    assert any(item_id in (m.get("title") or "")
               for m in ratified.get_json()["data"]["minutes"])
    closed = client.get("/api/meetings/MTG1").get_json()
    assert closed["data"]["actions"][0]["status"] == "Closed"


def test_a_declined_closure_returns_the_action_to_open(client):
    item_id = _meeting_with_action(client)
    _update(client, item_id, note="I think this is done", status=REQUESTED)
    declined = _reject(client, item_id, comments="Evidence does not cover the 2026 set.")
    assert declined.status_code == 200
    data = declined.get_json()["data"]
    assert data["actions"][0]["status"] == "Open"
    assert data["actions"][0]["updates"][-1]["note"] == "Evidence does not cover the 2026 set."
    assert any("Closure declined" in (m.get("title") or "") for m in data["minutes"])


def test_outstanding_actions_reach_across_the_committees_meetings(client, monkeypatch):
    """An action agreed at one meeting is what the next one has to review."""
    item_id = _meeting_with_action(client)
    _schedule(client, meeting_id="MTG2", date="2026-09-30")
    _close(client, monkeypatch, "MTG1")
    rows = client.get("/api/meetings/MTG2/outstanding-actions").get_json()
    assert [r["item_id"] for r in rows] == [item_id]
    assert rows[0]["meeting_id"] == "MTG1"

    _update(client, item_id, note="Done", status=REQUESTED)
    _ratify(client, item_id, meeting_id="MTG2", source_meeting_id="MTG1")
    assert client.get("/api/meetings/MTG2/outstanding-actions").get_json() == []


def test_an_empty_update_is_refused(client):
    """A dated entry that says nothing is noise in an append-only history."""
    item_id = _meeting_with_action(client)
    refused = _update(client, item_id)
    assert refused.status_code == 400


# --- What the endpoints refuse ------------------------------------------------

def test_an_update_against_a_meeting_or_action_that_is_not_there_is_404(client):
    _meeting_with_action(client)
    absent_meeting = client.post(
        "/api/meetings/MTG9/collections/actions/AC-001/updates",
        data={"note": "progress"}, content_type="multipart/form-data", headers=HEADERS)
    assert absent_meeting.status_code == 404
    assert _update(client, "AC-999", note="progress").status_code == 404


def test_evidence_the_platform_will_not_store_is_refused_with_the_update(client):
    """The update and its evidence are one record: storing the note and dropping
    the file would leave a history saying evidence was filed when it was not."""
    item_id = _meeting_with_action(client)
    refused = _update(client, item_id, note="Backtest output",
                      file=(io.BytesIO(b"MZ"), "backtest.exe"))
    assert refused.status_code == 400


def test_evidence_on_an_action_that_is_not_there_is_404(client):
    _meeting_with_action(client)
    assert client.get(
        "/api/meetings/MTG1/collections/actions/AC-999/evidence/x.pdf",
        headers=HEADERS).status_code == 404


def test_evidence_whose_file_has_gone_missing_is_404_not_a_500(client):
    item_id = _meeting_with_action(client)
    stored = _update(client, item_id, note="Backtest output",
                     file=(io.BytesIO(b"%PDF-1.4 backtest"), "backtest.pdf"))
    filename = stored.get_json()["data"]["actions"][0]["updates"][0]["filename"]
    upload_path(ACTION_EVIDENCE_SCOPE, filename).unlink()
    assert client.get(
        f"/api/meetings/MTG1/collections/actions/{item_id}/evidence/{filename}",
        headers=HEADERS).status_code == 404


def test_outstanding_actions_for_a_meeting_that_is_not_there_is_404(client):
    assert client.get("/api/meetings/MTG9/outstanding-actions").status_code == 404


def test_a_closure_cannot_be_ratified_at_a_meeting_that_is_not_there(client):
    item_id = _meeting_with_action(client, status=REQUESTED)
    assert _ratify(client, item_id, meeting_id="MTG9").status_code == 404


def test_a_closure_cannot_be_ratified_for_an_action_that_is_not_there(client):
    _meeting_with_action(client)
    assert _ratify(client, "AC-999").status_code == 404


def test_an_inquorate_meeting_cannot_ratify_a_closure(client):
    """Closing somebody's obligation is a decision, so it needs the committee that
    was actually in the room."""
    client.post("/api/reference/collections/mrc",
                json={"fields": {"value": "MRC-Q", "name": "MRC-Q", "level": "Company",
                                 "quorum_require_chair": "Yes",
                                 "quorum_require_secretary": "Yes",
                                 "quorum_min_voting": "3"},
                      "confirmed": True}, headers=HEADERS)
    _schedule(client, meeting_id="MTG-Q", mrc="MRC-Q")
    added = client.post("/api/meetings/MTG-Q/collections/actions",
                        json={"fields": {"description": "Re-run the backtest",
                                         "status": REQUESTED}, "confirmed": True},
                        headers=HEADERS)
    item_id = added.get_json()["data"]["actions"][0]["item_id"]
    refused = _ratify(client, item_id, meeting_id="MTG-Q")
    assert refused.status_code == 400
    assert "quorate" in refused.get_json()["error"]
