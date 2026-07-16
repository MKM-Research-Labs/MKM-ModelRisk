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
"""Tests for the meeting-quorum rule: the pure ``is_quorate`` helper and the
server-side gate that blocks sign-off decisions until a meeting is quorate."""
from __future__ import annotations

from src.web.api_mrc._quorum import is_quorate
from tests.web.conftest import HEADERS
from tests.web.test_mrc_signoff_api import (
    _register_subject_model,
    _request_signoff,
    _schedule_meeting,
    _signoff_item,
)


def _meeting(participants, **overrides):
    d = {
        "chair": "Cara Chair", "secretary": "Sam Sec",
        "voting_members": ["Val One", "Vic Two"],
        "participants": participants,
    }
    d.update(overrides)
    return d


def _attended(*names):
    return [{"name": n, "status": "Attended"} for n in names]


def test_quorate_when_chair_secretary_and_two_voting_attend():
    d = _meeting(_attended("Cara Chair", "Sam Sec", "Val One", "Vic Two"))
    assert is_quorate(d) is True


def test_not_quorate_when_chair_absent():
    d = _meeting(_attended("Sam Sec", "Val One", "Vic Two"))
    assert is_quorate(d) is False


def test_not_quorate_when_secretary_absent():
    # Chair present so the check advances past the chair rule to the secretary one.
    d = _meeting(_attended("Cara Chair", "Val One", "Vic Two"))
    assert is_quorate(d) is False


def test_not_quorate_when_too_few_voting():
    d = _meeting(_attended("Cara Chair", "Sam Sec", "Val One"))
    assert is_quorate(d) is False


def test_requirements_can_be_switched_off():
    # No chair/secretary required and zero voting needed → quorate with nobody.
    d = _meeting([], quorum_require_chair="No",
                 quorum_require_secretary="No", quorum_min_voting="0")
    assert is_quorate(d) is True


def test_non_numeric_min_voting_defaults_to_two():
    d = _meeting(_attended("Cara Chair", "Sam Sec", "Val One"),
                 quorum_min_voting="lots")
    assert is_quorate(d) is False  # default of 2 not met with a single voter


def test_guest_attendee_counts_under_their_own_role():
    # A participant not on the roster is credited with their stated role; here an
    # extra voting attendee makes up the second voting seat.
    d = _meeting(
        _attended("Cara Chair", "Sam Sec", "Val One")
        + [{"name": "Gwen Guest", "role": "Voting", "status": "Attended"}]
    )
    assert is_quorate(d) is True


# --- the server-side gate: sign-off is refused until the meeting is quorate ---

def _seed_mrc_strict(client, value="MRC-STRICT"):
    """A committee with the default quorum (Chair + Secretary + 2 voting) and no
    attended roster, so its meetings are never quorate."""
    return client.post(
        "/api/reference/collections/mrc",
        json={"fields": {"value": value, "name": value, "level": "Company"},
              "confirmed": True}, headers=HEADERS,
    )


def test_signoff_blocked_until_meeting_is_quorate(client):
    # With a strict committee and no attendance, both approve and reject are
    # refused server-side and the subject's rating is left untouched.
    _seed_mrc_strict(client)
    _register_subject_model(client)                     # Amber
    _schedule_meeting(client, mrc="MRC-STRICT")
    _request_signoff(client)                             # proposes Green
    agenda_id = _signoff_item(client)["item_id"]
    approve = client.post(
        f"/api/meetings/MTG1/agenda/{agenda_id}/approve-signoff",
        json={"confirmed": True}, headers=HEADERS,
    )
    assert approve.status_code == 400
    assert "quorate" in approve.get_json()["error"]
    reject = client.post(
        f"/api/meetings/MTG1/agenda/{agenda_id}/reject-signoff",
        json={"confirmed": True}, headers=HEADERS,
    )
    assert reject.status_code == 400
    assert "quorate" in reject.get_json()["error"]
    # No decision went through: the rating is unchanged and the item still Pending.
    assert client.get("/api/models/M1").get_json()["data"]["rag_rating"] == "Amber"
    assert _signoff_item(client)["status"] == "Pending"
