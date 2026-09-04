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
"""The committee ratifies hibernation for a Product.

A Product was the last of the five subjects whose retirement nobody ratified: its
Danger tab hibernated the record the moment its owner pressed the button, and a
retired one was told nothing further could be changed — which is the whole problem,
because asking to come back is a thing that has to be changeable.

It now takes the journey the model, ML Application and AI System take. The wrinkle
particular to a Product is that retiring overwrites its ``status`` field with
"Retired" (the other three deliberately leave the institution's vocabulary alone),
so reactivating has to put back the word it displaced. That is the last two tests.
"""
from __future__ import annotations

from src.web._signoff_subject import PRODUCT_SUBJECT
from tests.web._signoff_flows import (
    _schedule_meeting,
    _seed_mrc,
    decide,
    request_reactivate,
    request_retire,
    signoff_item_of_kind,
)
from tests.web.conftest import HEADERS

_P = "/api/products"
_ID = "Product-0001"


def _register(client, product_id=_ID, **overrides):
    client.post("/api/models",
                json={"model_id": "MKM-AN-001", "name": "Analytics", "confirmed": True},
                headers=HEADERS)
    return client.post("/api/products",
                       json={"product_id": product_id, "product": "Government Bond",
                             "fields": {"calculating_agent": "Murex", **overrides},
                             "confirmed": True}, headers=HEADERS)


def _ready(client, **overrides):
    """A committee, a Product, and a meeting for it to be decided at."""
    _seed_mrc(client)
    _register(client, **overrides)
    _schedule_meeting(client)


def _status(client, value):
    return client.post(f"{_P}/{_ID}/field",
                       json={"field": "status", "value": value, "confirmed": True},
                       headers=HEADERS)


def test_a_product_can_be_hibernated_and_brought_back():
    """The last subject to carry both halves. ``supports`` is what stops the
    committee being offered a decision the subject cannot carry out."""
    assert PRODUCT_SUBJECT.supports("retire")
    assert PRODUCT_SUBJECT.supports("reactivate")
    # The name a person reads: it goes into the minute the committee signs.
    assert PRODUCT_SUBJECT.noun == "Product"


def test_requesting_retire_does_not_hibernate_the_product(client):
    """The governance guarantee: asking is not deciding."""
    _ready(client)
    assert request_retire(client, _ID, api=_P).status_code == 201
    product = client.get(f"{_P}/{_ID}").get_json()
    assert product["retired"] is False, "it must stay active until ratified"
    request = product["data"]["signoff_requests"][0]
    assert request["kind"] == "retire" and request["status"] == "Attached"
    assert signoff_item_of_kind(client, "retire")["subject_product_id"] == _ID


def test_the_committee_hibernates_a_product_and_minutes_it(client):
    _ready(client)
    request_retire(client, _ID, api=_P)
    payload = decide(client, signoff_item_of_kind(client, "retire")["item_id"]).get_json()
    assert payload["product"]["retired"] is True
    history = payload["product"]["data"]["signoff_history"]
    assert history[-1]["kind"] == "retire" and history[-1]["outcome"] == "Approved"
    minute = next(m for m in payload["meeting"]["data"]["minutes"]
                  if m.get("product_id") == _ID)
    assert "Product owner" in minute["text"]


def test_rejecting_a_retire_leaves_the_product_active(client):
    _ready(client)
    request_retire(client, _ID, api=_P)
    payload = decide(client, signoff_item_of_kind(client, "retire")["item_id"],
                     outcome="reject").get_json()
    assert payload["product"]["retired"] is False
    assert payload["product"]["data"]["signoff_history"][-1]["outcome"] == "Rejected"


def test_a_hibernated_product_can_be_brought_back_through_the_committee(client):
    _ready(client)
    request_retire(client, _ID, api=_P)
    decide(client, signoff_item_of_kind(client, "retire")["item_id"])
    assert client.get(f"{_P}/{_ID}").get_json()["retired"] is True

    # A hibernated Product is read-only but can still raise this one request —
    # otherwise there is no way back.
    assert request_reactivate(client, _ID, api=_P).status_code == 201
    back = decide(client, signoff_item_of_kind(client, "reactivate")["item_id"]).get_json()
    assert back["product"]["retired"] is False
    assert back["product"]["data"]["signoff_history"][-1]["kind"] == "reactivate"
    # Editable again once it is back in the estate.
    assert _status(client, "Suspended").status_code == 200


def test_the_state_the_request_needs_is_checked(client):
    _ready(client)
    assert request_reactivate(client, _ID, api=_P).status_code == 400   # not retired
    request_retire(client, _ID, api=_P)
    decide(client, signoff_item_of_kind(client, "retire")["item_id"])
    assert request_retire(client, _ID, api=_P).status_code == 400       # already gone


def test_an_unknown_product_is_a_404(client):
    assert request_retire(client, "NOPE", api=_P).status_code == 404
    assert request_retire(client, "NOPE", api=_P).get_json()["error"] == "Product not found"


def test_there_is_no_way_to_retire_a_product_outside_the_committee(client):
    """The Danger tab used to POST here. The route is gone, not merely unlinked."""
    _register(client)
    assert client.post(f"{_P}/{_ID}/retire", json={"confirmed": True},
                       headers=HEADERS).status_code == 404


# --- the wrinkle particular to a Product: its status field ---------------------
#
# The fallback for a Product retired before the status was recorded is a domain
# question, so it is tested against the rules and the fold in
# tests/governance/test_product.py rather than through six HTTP round trips.


def test_reactivating_restores_the_status_the_retire_displaced(client):
    """Retiring a Product overwrites ``status`` with "Retired". Bringing it back has
    to put the previous word back, or a live Product reads as retired on every screen
    that shows the field."""
    _ready(client)
    _status(client, "Active")
    request_retire(client, _ID, api=_P)
    decide(client, signoff_item_of_kind(client, "retire")["item_id"])
    assert client.get(f"{_P}/{_ID}").get_json()["data"]["status"] == "Retired"

    request_reactivate(client, _ID, api=_P)
    decide(client, signoff_item_of_kind(client, "reactivate")["item_id"])
    product = client.get(f"{_P}/{_ID}").get_json()
    assert product["retired"] is False
    assert product["data"]["status"] == "Active", "the status it had before hibernation"
