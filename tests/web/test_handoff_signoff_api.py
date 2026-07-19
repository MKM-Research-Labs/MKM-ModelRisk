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
"""The handoff compatibility sign-off — the light MRC ratification (Phase B.1b).

A handoff rides the same request → agenda → ratify machinery as a rating sign-off,
routed to the consumer model's committee. Approving it stamps the MRC sign-off, so
the handoff's derived status flips to Approved.
"""
from __future__ import annotations

from tests.web.conftest import HEADERS
from tests.web._signoff_flows import _schedule, _seed_mrc


def _register(client, model_id):
    return client.post(
        "/api/models",
        json={"model_id": model_id, "name": model_id, "confirmed": True},
        headers=HEADERS,
    )


def _edge_and_handoff(client, from_model="A", to_model="B"):
    _register(client, from_model)
    _register(client, to_model)
    client.post(
        f"/api/models/{from_model}/collections/dependencies",
        json={"fields": {"direction": "downstream", "model_id": to_model}, "confirmed": True},
        headers=HEADERS,
    )
    return client.post(
        "/api/handoffs",
        json={"from_model": from_model, "to_model": to_model, "confirmed": True},
        headers=HEADERS,
    )


def _request(client, hid="A~B"):
    return client.post(f"/api/handoffs/{hid}/request-signoff",
                       json={"confirmed": True}, headers=HEADERS)


def _handoff_agenda_item(client, meeting_id="MTG1"):
    agenda = client.get(f"/api/meetings/{meeting_id}").get_json()["data"]["agenda"]
    return next(a for a in agenda if a.get("subject_handoff_id"))


def test_owner_field_route_refuses_non_prose_fields(client):
    _edge_and_handoff(client)
    # The sign-off stamp is committee-only; the owner route must not set it.
    resp = client.post("/api/handoffs/A~B/field",
                       json={"field": "mrc_signoff_meeting", "value": "MTG1", "confirmed": True},
                       headers=HEADERS)
    assert resp.status_code == 400
    assert client.get("/api/handoffs/A~B").get_json()["data"]["status"] == "Draft"


def test_request_signoff_queues_and_marks_pending(client):
    _seed_mrc(client)
    _edge_and_handoff(client)
    resp = _request(client)
    assert resp.status_code == 201
    assert resp.get_json()["data"]["status"] == "Pending sign-off"


def test_request_without_a_covering_mrc_is_400(client):
    _edge_and_handoff(client)  # no MRC seeded
    assert _request(client).status_code == 400


def test_request_signoff_on_unknown_handoff_is_404(client):
    assert _request(client, hid="no~such").status_code == 404


def test_mrc_approval_stamps_the_handoff_approved(client):
    _seed_mrc(client)
    _edge_and_handoff(client)
    _schedule(client)          # a scheduled meeting of the covering MRC
    _request(client)           # attaches to that meeting immediately
    item = _handoff_agenda_item(client)
    assert item["signoff_kind"] == "handoff"

    approve = client.post(
        f"/api/meetings/MTG1/agenda/{item['item_id']}/approve-signoff",
        json={"confirmed": True}, headers=HEADERS,
    )
    assert approve.status_code == 200
    handoff = client.get("/api/handoffs/A~B").get_json()["data"]
    assert handoff["status"] == "Approved"
    assert handoff["mrc_signoff_meeting"] == "MTG1"


def test_a_handoff_agenda_item_is_minuted_on_approval(client):
    _seed_mrc(client)
    _edge_and_handoff(client)
    _schedule(client)
    _request(client)
    item = _handoff_agenda_item(client)
    client.post(f"/api/meetings/MTG1/agenda/{item['item_id']}/approve-signoff",
                json={"confirmed": True}, headers=HEADERS)
    minutes = client.get("/api/meetings/MTG1").get_json()["data"].get("minutes") or []
    assert any(m.get("handoff_id") == "A~B" for m in minutes)
