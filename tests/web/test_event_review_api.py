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
"""Operational events feeding up to the MRC (RACI feed-up, step 3).

Scheduling a meeting allocates the committee's products' unreceived events as
agenda items; the committee then receives each one — stamping it Received with
comments, recording action items on the product, and minuting the decision.
"""
from __future__ import annotations

from tests.web.conftest import HEADERS
from tests.web._signoff_flows import _schedule, _seed_mrc


def _live_model(client, model_id="MKM-AN-001"):
    client.post("/api/models", json={"model_id": model_id, "name": "Analytics", "confirmed": True},
                headers=HEADERS)


def _register_product(client, product_id="PRD-1"):
    _live_model(client)
    return client.post("/api/products", json={
        "product_id": product_id, "product": "Bond Book",
        "fields": {"calculating_agent": "Murex"}, "confirmed": True}, headers=HEADERS)


def _add_event(client, product_id="PRD-1", description="Market-data feed outage"):
    return client.post(f"/api/products/{product_id}/collections/operational_failure_events",
                       json={"fields": {"date": "2026-06-01", "description": description},
                             "confirmed": True}, headers=HEADERS)


def _event_agenda_item(client, meeting_id="MTG1"):
    agenda = client.get(f"/api/meetings/{meeting_id}").get_json()["data"]["agenda"]
    return next(a for a in agenda if a.get("subject_event_id"))


def test_scheduling_allocates_product_events_to_the_agenda(client):
    _seed_mrc(client)
    _register_product(client)
    _add_event(client)
    _schedule(client)  # MTG1 for MRC-CO — allocation runs on schedule
    item = _event_agenda_item(client)
    assert item["subject_product_id"] == "PRD-1"
    assert "Operational event review: PRD-1" in item["title"]


def test_a_received_event_is_not_re_allocated(client):
    # Second scheduled meeting shouldn't re-raise an already-received event.
    _seed_mrc(client)
    _register_product(client)
    _add_event(client)
    _schedule(client)
    item = _event_agenda_item(client)
    client.post(f"/api/meetings/MTG1/agenda/{item['item_id']}/receive-event",
                json={"comments": "ok", "confirmed": True}, headers=HEADERS)
    _schedule(client, meeting_id="MTG2", date="2026-09-30")
    agenda2 = client.get("/api/meetings/MTG2").get_json()["data"]["agenda"]
    assert not [a for a in agenda2 if a.get("subject_event_id")]


def test_receive_event_stamps_received_records_actions_and_minutes(client):
    _seed_mrc(client)
    _register_product(client)
    _add_event(client)
    _schedule(client)
    item = _event_agenda_item(client)
    resp = client.post(
        f"/api/meetings/MTG1/agenda/{item['item_id']}/receive-event",
        json={"comments": "Understood — monitoring added",
              "actions": [{"description": "Add a feed heartbeat alarm"}], "confirmed": True},
        headers=HEADERS,
    )
    assert resp.status_code == 200

    product = client.get("/api/products/PRD-1").get_json()["data"]
    event = product["operational_failure_events"][0]
    assert event["mrc_status"] == "Received"
    assert "monitoring" in event["review_comments"] and event["mrc_meeting"] == "MTG1"
    assert any(a["description"] == "Add a feed heartbeat alarm" for a in product.get("actions", []))

    meeting = client.get("/api/meetings/MTG1").get_json()["data"]
    done = next(a for a in meeting["agenda"] if a["item_id"] == item["item_id"])
    assert done["status"] == "Completed"
    assert any(m.get("product_id") == "PRD-1" for m in meeting.get("minutes", []))


def test_receive_event_needs_confirmation(client):
    _seed_mrc(client)
    _register_product(client)
    _add_event(client)
    _schedule(client)
    item = _event_agenda_item(client)
    resp = client.post(f"/api/meetings/MTG1/agenda/{item['item_id']}/receive-event",
                       json={"comments": "x"}, headers=HEADERS)
    assert resp.status_code == 409  # ConfirmationRequired


def test_receive_on_a_non_event_agenda_item_is_400(client):
    _seed_mrc(client)
    _schedule(client)
    agenda = client.get("/api/meetings/MTG1").get_json()["data"]["agenda"]
    standing = agenda[0]  # a standing item, not an event review
    resp = client.post(f"/api/meetings/MTG1/agenda/{standing['item_id']}/receive-event",
                       json={"confirmed": True}, headers=HEADERS)
    assert resp.status_code == 400


def test_receive_unknown_meeting_or_item_is_404(client):
    _seed_mrc(client)
    _schedule(client)
    assert client.post("/api/meetings/NONE/agenda/AG-1/receive-event",
                       json={"confirmed": True}, headers=HEADERS).status_code == 404
    assert client.post("/api/meetings/MTG1/agenda/NO-ITEM/receive-event",
                       json={"confirmed": True}, headers=HEADERS).status_code == 404


def test_receive_without_comments_or_action_descriptions(client):
    _seed_mrc(client)
    _register_product(client)
    _add_event(client)
    _schedule(client)
    item = _event_agenda_item(client)
    # No comments, and an action with no description (skipped) — still received cleanly.
    resp = client.post(f"/api/meetings/MTG1/agenda/{item['item_id']}/receive-event",
                       json={"actions": [{"owner": "someone"}], "confirmed": True}, headers=HEADERS)
    assert resp.status_code == 200
    product = client.get("/api/products/PRD-1").get_json()["data"]
    assert product["operational_failure_events"][0]["mrc_status"] == "Received"
    assert not product.get("actions")  # the description-less action was skipped


def test_long_event_description_is_truncated_in_the_agenda_title(client):
    _seed_mrc(client)
    _register_product(client)
    _add_event(client, description="x" * 90)
    _schedule(client)
    assert _event_agenda_item(client)["title"].endswith("...")


def test_events_are_only_allocated_to_the_owning_committee(client):
    # A product under a division committee must not surface on a *company* meeting.
    _seed_mrc(client)  # MRC-CO (Company)
    _seed_mrc(client, value="MRC-MKT", level="Division", scope_value="Markets")
    _live_model(client)
    client.post("/api/products", json={
        "product_id": "PRD-MKT", "product": "Markets Book",
        "fields": {"calculating_agent": "Murex", "division": "Markets"}, "confirmed": True},
        headers=HEADERS)
    _add_event(client, product_id="PRD-MKT")
    _schedule(client, mrc="MRC-CO")  # company meeting
    agenda = client.get("/api/meetings/MTG1").get_json()["data"]["agenda"]
    assert not [a for a in agenda if a.get("subject_product_id") == "PRD-MKT"]


def test_allocate_skips_a_meeting_with_no_committee():
    from src.web._event_review import allocate_events_for_meeting
    # No committee on the meeting -> nothing to allocate (context is unused here).
    assert allocate_events_for_meeting(None, {"meeting_id": "X", "data": {}}) == 0


def test_allocate_is_idempotent_on_the_same_meeting(client):
    from src.command.dispatch import context_from_headers
    from src.governance.mrc import get_meeting_enriched
    from src.web._event_review import allocate_events_for_meeting
    _seed_mrc(client)
    _register_product(client)
    _add_event(client)
    _schedule(client)
    ctx = context_from_headers({"X-Auth-Request-User": "alice@corp"}, confirmed=True)
    # The event is already on MTG1's agenda from scheduling — a re-run adds nothing.
    assert allocate_events_for_meeting(ctx, get_meeting_enriched("MTG1")) == 0


def test_receive_requires_a_quorate_meeting(client):
    client.post("/api/reference/collections/mrc",
                json={"fields": {"value": "MRC-Q", "name": "MRC-Q", "level": "Company",
                                 "quorum_require_chair": "No", "quorum_require_secretary": "No",
                                 "quorum_min_voting": "2"}, "confirmed": True}, headers=HEADERS)
    _register_product(client)
    _add_event(client)
    _schedule(client, mrc="MRC-Q")  # no attendees -> not quorate
    item = _event_agenda_item(client)
    resp = client.post(f"/api/meetings/MTG1/agenda/{item['item_id']}/receive-event",
                       json={"confirmed": True}, headers=HEADERS)
    assert resp.status_code == 400
