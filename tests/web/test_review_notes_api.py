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
"""The record of challenge: the owner/reviewer thread on a review stage.

This is not a chat feature. It is the evidence that a model was challenged, it is
printed in the report the committee receives, and its value rests entirely on
nobody being able to tidy it up afterwards. These tests hold that: what is posted
stays posted, a challenge is answered rather than closed, and who said it is taken
from the signed-in identity rather than from whatever the caller claimed.
"""
from __future__ import annotations

from src.web.api_models_review import challenges, open_challenges
from tests.web.conftest import HEADERS

def _register(client):
    """A model with a named owner and reviewer, so a note's role can be derived."""
    return client.post(
        "/api/models",
        json={"model_id": "M1", "name": "Alpha", "confirmed": True,
              "fields": {"owner": "owner@corp", "peer_reviewer": "rev@corp"}},
        headers=HEADERS,
    )


def _note(client, stage="questions", text="Looks thin", kind="Note", resolves="", actor=None):
    headers = dict(HEADERS)
    if actor:
        headers["X-Auth-Request-User"] = actor
    return client.post(
        "/api/models/M1/review/note",
        json={"stage": stage, "text": text, "kind": kind, "resolves": resolves},
        headers=headers,
    )


def _notes(client):
    return client.get("/api/models/M1").get_json()["data"]["review_notes"]


def test_a_note_is_stamped_with_its_author_and_side_of_the_review(client):
    """The role is derived from the model's own owner and reviewer — "who
    challenged whom" must not be a matter of what somebody picked from a dropdown."""
    _register(client)
    assert _note(client, actor="rev@corp").status_code == 201
    assert _note(client, text="Fair point", actor="owner@corp").status_code == 201
    posted = _notes(client)
    assert [n["author_role"] for n in posted] == ["Reviewer", "Owner"]
    assert [n["author"] for n in posted] == ["rev@corp", "owner@corp"]
    assert all(n["posted_at"] for n in posted)


def test_someone_who_is_neither_is_a_participant(client):
    """The platform attributes; it does not police who may speak."""
    _register(client)
    _note(client, actor="cro@corp")
    assert _notes(client)[0]["author_role"] == "Participant"


def test_the_reviewer_is_recognised_through_the_people_directory(client):
    """A model names its reviewer by directory name; the signed-in identity is an
    email. Without the directory joining the two, every note in the estate would be
    filed as a Participant and the record would show a review nobody carried out."""
    client.post("/api/reference/collections/people",
                json={"fields": {"name": "Priya Anand", "email": "priya@corp"},
                      "confirmed": True}, headers=HEADERS)
    client.post("/api/models",
                json={"model_id": "M2", "name": "Beta", "confirmed": True,
                      "fields": {"peer_reviewer": "Priya Anand"}}, headers=HEADERS)
    headers = {**HEADERS, "X-Auth-Request-User": "priya@corp"}
    client.post("/api/models/M2/review/note",
                json={"stage": "questions", "text": "Not convinced by the benchmark"},
                headers=headers)
    posted = client.get("/api/models/M2").get_json()["data"]["review_notes"]
    assert posted[0]["author_role"] == "Reviewer"
    assert posted[0]["author"] == "priya@corp"


def test_a_challenge_is_open_until_a_note_answers_it(client):
    _register(client)
    _note(client, text="The benchmark is not comparable", kind="Challenge", actor="rev@corp")
    data = client.get("/api/models/M1").get_json()["data"]
    raised = challenges(data)
    assert [c["state"] for c in raised] == ["Open"]
    assert len(open_challenges(data)) == 1

    _note(client, text="Swapped for a like-for-like benchmark",
          resolves=raised[0]["item_id"], actor="owner@corp")
    data = client.get("/api/models/M1").get_json()["data"]
    assert [c["state"] for c in challenges(data)] == ["Resolved"]
    assert open_challenges(data) == []
    assert challenges(data)[0]["answered_by"]


def test_a_note_cannot_be_edited_or_deleted(client):
    """A challenge that could be tidied away afterwards is not evidence of
    anything. The domain refuses, so it does not rest on the console hiding a button."""
    _register(client)
    _note(client, text="The benchmark is not comparable", kind="Challenge", actor="rev@corp")
    item_id = _notes(client)[0]["item_id"]

    edit = client.post(
        f"/api/models/M1/collections/review_notes/{item_id}",
        json={"fields": {"text": "Actually it is fine"}, "confirmed": True}, headers=HEADERS,
    )
    assert edit.status_code == 400
    assert "append-only" in edit.get_json()["error"]

    delete = client.post(
        f"/api/models/M1/collections/review_notes/{item_id}/delete",
        json={"confirmed": True}, headers=HEADERS,
    )
    assert delete.status_code == 400
    assert _notes(client)[0]["text"] == "The benchmark is not comparable"


def test_an_empty_note_is_refused(client):
    _register(client)
    assert _note(client, text="   ").status_code == 400


def test_an_unknown_stage_or_kind_is_refused(client):
    _register(client)
    assert _note(client, stage="elsewhere").status_code == 400
    assert _note(client, kind="Grumble").status_code == 400


def test_a_note_on_an_unknown_model_is_404(client):
    assert client.post(
        "/api/models/NOPE/review/note",
        json={"stage": "questions", "text": "hello"}, headers=HEADERS,
    ).status_code == 404
