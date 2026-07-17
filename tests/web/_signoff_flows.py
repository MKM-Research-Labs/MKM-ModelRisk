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
"""Shared flows for the MRC sign-off API tests.

The rating, retire and reactivate journeys all need the same scaffolding — a
committee, a subject, a scheduled meeting — so it lives here once rather than
being copied per test module.
"""
from __future__ import annotations

from tests.web.conftest import HEADERS


def _seed_mrc(client, value="MRC-CO", level="Company", scope_value=None):
    """A Company-level MRC covering every model. Quorum is switched off so its
    meetings are quorate without an attended roster — these tests exercise
    sign-off mechanics; the quorum gate is covered in test_mrc_quorum.py."""
    fields = {"value": value, "name": value, "level": level,
              "quorum_require_chair": "No", "quorum_require_secretary": "No",
              "quorum_min_voting": "0"}
    if scope_value:
        fields["scope_value"] = scope_value
    return client.post(
        "/api/reference/collections/mrc",
        json={"fields": fields, "confirmed": True}, headers=HEADERS,
    )


def _schedule(client, meeting_id="MTG1", mrc="MRC-CO", date="2026-06-30"):
    return client.post(
        "/api/meetings",
        json={"meeting_id": meeting_id, "title": "Q2 MRC", "date": date,
              "fields": {"mrc": mrc}, "confirmed": True},
        headers=HEADERS,
    )


def _add(client, collection, fields):
    return client.post(
        "/api/meetings/MTG1/collections/" + collection,
        json={"fields": fields, "confirmed": True}, headers=HEADERS,
    )


def _schedule_meeting(client, meeting_id="MTG1", mrc="MRC-CO", date="2026-09-15"):
    return client.post(
        "/api/meetings",
        json={"meeting_id": meeting_id, "title": "Q3", "date": date,
              "fields": {"mrc": mrc}, "confirmed": True},
        headers=HEADERS,
    )


def _register_subject_model(client, model_id="M1", **fields):
    return client.post(
        "/api/models",
        json={"model_id": model_id, "name": "Subject",
              "fields": {"rag_rating": "Amber", **fields}, "confirmed": True},
        headers=HEADERS,
    )


def _request_signoff(client, model_id="M1", proposed_rag="Green"):
    return client.post(
        f"/api/models/{model_id}/request-signoff",
        json={"proposed_rag": proposed_rag, "confirmed": True},
        headers=HEADERS,
    )


def _signoff_agenda_items(agenda):
    """The sign-off items on a meeting's agenda — every meeting also seeds the
    five standing agenda items, so a sign-off is never alone or necessarily first."""
    return [a for a in agenda if a.get("subject_model_id") or a.get("subject_product_id")]


def _signoff_item(client, meeting_id="MTG1"):
    agenda = client.get(f"/api/meetings/{meeting_id}").get_json()["data"]["agenda"]
    return _signoff_agenda_items(agenda)[0]


def request_retire(client, model_id="M1"):
    return client.post(f"/api/models/{model_id}/request-retire",
                       json={"confirmed": True}, headers=HEADERS)


def request_reactivate(client, model_id="M1"):
    return client.post(f"/api/models/{model_id}/request-reactivate",
                       json={"confirmed": True}, headers=HEADERS)


def decide(client, agenda_id, outcome="approve", meeting_id="MTG1"):
    """Approve/reject a sign-off item. The committee's decision is gated, so it
    always carries the confirmation."""
    return client.post(f"/api/meetings/{meeting_id}/agenda/{agenda_id}/{outcome}-signoff",
                       json={"confirmed": True}, headers=HEADERS)
