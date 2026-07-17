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
"""The committee ratifies hibernation: retire / reactivate round-trips."""
from __future__ import annotations

from tests.web._signoff_flows import (
    _add,
    _register_subject_model,
    _schedule_meeting,
    _seed_mrc,
    _signoff_item,
    decide,
    request_reactivate,
    request_retire,
)
from tests.web.conftest import HEADERS


# --- Retire / reactivate: the committee ratifies hibernation ------------------


def test_requesting_retire_does_not_hibernate_until_the_mrc_approves(client):
    """The governance guarantee: asking is not deciding."""
    _seed_mrc(client)
    _register_subject_model(client)
    _schedule_meeting(client)
    assert request_retire(client).status_code == 201
    model = client.get("/api/models/M1").get_json()
    assert model["retired"] is False, "model must stay active until ratified"
    request = model["data"]["signoff_requests"][0]
    assert request["kind"] == "retire" and request["status"] == "Attached"
    # It reaches the committee as its own agenda item.
    assert _signoff_item(client)["signoff_kind"] == "retire"


def test_approving_a_retire_hibernates_the_model_and_minutes_it(client):
    _seed_mrc(client)
    _register_subject_model(client)
    _schedule_meeting(client)
    request_retire(client)
    response = decide(client, _signoff_item(client)["item_id"])
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["model"]["retired"] is True
    history = payload["model"]["data"]["signoff_history"]
    assert history[-1]["kind"] == "retire" and history[-1]["outcome"] == "Approved"
    # A retire is not a rating sign-off, so it must not stamp the rating fields.
    assert not payload["model"]["data"].get("mrc_signoff_meeting")
    assert payload["model"]["data"]["rag_rating"] == "Amber"
    minutes = payload["meeting"]["data"]["minutes"]
    assert any("hibernated" in m["text"] for m in minutes)


def test_rejecting_a_retire_leaves_the_model_active(client):
    _seed_mrc(client)
    _register_subject_model(client)
    _schedule_meeting(client)
    request_retire(client)
    payload = decide(client, _signoff_item(client)["item_id"], outcome="reject").get_json()
    assert payload["model"]["retired"] is False
    assert payload["model"]["data"]["signoff_history"][-1]["outcome"] == "Rejected"


def test_a_hibernated_model_can_be_brought_back_through_the_committee(client):
    """Hibernation reverses: a retired model can still raise a reactivate request
    (it is otherwise read-only) and the committee can restore it."""
    _seed_mrc(client)
    _register_subject_model(client)
    _schedule_meeting(client)
    request_retire(client)
    decide(client, _signoff_item(client)["item_id"])
    assert client.get("/api/models/M1").get_json()["retired"] is True

    # A retired model is read-only, but it can still raise this one request —
    # otherwise there would be no way back. It attaches to the committee's next
    # scheduled meeting, which is the one already open.
    assert request_reactivate(client).status_code == 201
    agenda = client.get("/api/meetings/MTG1").get_json()["data"]["agenda"]
    item = next(a for a in agenda if a.get("signoff_kind") == "reactivate")
    payload = decide(client, item["item_id"]).get_json()
    assert payload["model"]["retired"] is False, "the committee can bring it back"
    assert payload["model"]["data"]["signoff_history"][-1]["kind"] == "reactivate"
    # Editing works again once it is back in the active inventory.
    assert client.post("/api/models/M1/field",
                       json={"field": "methodology", "value": "OLS", "confirmed": True},
                       headers=HEADERS).status_code == 200


def test_cannot_request_retire_twice_or_reactivate_an_active_model(client):
    _seed_mrc(client)
    _register_subject_model(client)
    _schedule_meeting(client)
    assert request_reactivate(client).status_code == 400   # it is not retired
    request_retire(client)
    decide(client, _signoff_item(client)["item_id"])
    assert request_retire(client).status_code == 400       # already hibernated


def test_request_retire_rejects_unknown_model(client):
    assert request_retire(client, model_id="NOPE").status_code == 404


def test_request_retire_blocked_without_a_covering_mrc(client):
    _register_subject_model(client)   # no MRC configured at all
    response = request_retire(client)
    assert response.status_code == 400
    assert "MRC" in response.get_json()["error"]


def test_a_decision_the_subject_cannot_carry_out_is_rejected(client):
    """A product has no reactivate command, so the committee must not be able to
    ratify one against it — the guard is server-side, not just a hidden button."""
    _seed_mrc(client)
    _schedule_meeting(client)
    item = _add(client, "agenda", {
        "title": "Reactivate: P1", "subject_product_id": "P1",
        "signoff_kind": "reactivate", "status": "Pending",
    }).get_json()["data"]["agenda"][-1]
    response = decide(client, item["item_id"])
    assert response.status_code == 400
    assert "cannot be the subject of a reactivate decision" in response.get_json()["error"]
