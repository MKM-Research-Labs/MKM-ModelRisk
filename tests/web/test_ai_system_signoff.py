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
"""An AI System's rating goes to the committee, and the committee's word is minuted.

The ML twin of this exists; the AI one did not, which is how the defect below
survived. An approved sign-off writes its minute under the subject's own id field,
and the minutes collection spec had no ``ai_system_id`` — so *every* ratified AI
System decision was refused at the point of recording itself, rating included. The
request side was tested and passed; nothing walked as far as the approval.

So the last test here is the one that matters: it approves, and reads the minute.
"""
from __future__ import annotations

from src.web._signoff_subject import AI_SYSTEM_SUBJECT, SUBJECTS
from tests.web._signoff_flows import (
    _schedule_meeting,
    _seed_mrc,
    decide,
    signoff_item_of_kind,
)
from tests.web.test_mrc_retire_aiml_api import register_ai
from tests.web.conftest import HEADERS

_AI = "/api/ai-systems"


def _propose(client, ai_system_id="AIS-0001", **body):
    return client.post(f"{_AI}/{ai_system_id}/request-signoff",
                       json={"proposed_rag": "Green", "confirmed": True, **body},
                       headers=HEADERS)


def test_an_ai_system_is_a_subject_the_committee_knows():
    """A fifth registration, not a fifth route: the routing is written once against
    the Subject adapter and this joins it."""
    assert AI_SYSTEM_SUBJECT in SUBJECTS
    assert AI_SYSTEM_SUBJECT.agenda_id_field == "subject_ai_system_id"
    # The name a person reads, not the machine key — it goes into signed minutes.
    assert AI_SYSTEM_SUBJECT.noun == "AI System"


def test_an_unknown_record_is_a_404(client):
    assert _propose(client, "NOPE").status_code == 404


def test_a_proposal_needs_a_rating(client):
    register_ai(client)
    assert _propose(client, proposed_rag=None).status_code == 400


def test_a_proposal_without_a_committee_is_refused(client):
    """A rating nobody signs off is not a rating that has been through governance."""
    register_ai(client, division="Nowhere")
    response = _propose(client)
    assert response.status_code == 400
    assert "no MRC committee covers" in response.get_json()["error"]


def test_the_stored_rating_does_not_move_when_a_proposal_is_raised(client):
    _seed_mrc(client)
    register_ai(client, rag_rating="Amber")
    _schedule_meeting(client)
    assert _propose(client).status_code == 201
    record = client.get(f"{_AI}/AIS-0001").get_json()
    assert record["data"]["rag_rating"] == "Amber", "the owner proposes; the MRC decides"
    request = record["data"]["signoff_requests"][0]
    assert request["kind"] == "rag" and request["proposed_rag"] == "Green"


def test_an_approved_rating_moves_and_is_minuted_under_the_ai_system(client):
    """The regression test for the defect in this module's docstring.

    A minute is written inside the approval, so a record type the minutes spec does
    not know does not merely go unminuted — the whole decision is refused. Reading
    the minute back is what proves the field is there.
    """
    _seed_mrc(client)
    register_ai(client, rag_rating="Amber")
    _schedule_meeting(client)
    _propose(client)
    payload = decide(client, signoff_item_of_kind(client, "rag")["item_id"]).get_json()
    assert payload["ai_system"]["data"]["rag_rating"] == "Green"
    minutes = payload["meeting"]["data"]["minutes"]
    minute = next(m for m in minutes if m.get("ai_system_id") == "AIS-0001")
    # Named as a person would name it. ``subject.kind`` would read "ai_system owner"
    # in a minute the committee signs.
    assert "AI System owner" in minute["text"]
