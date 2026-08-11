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
"""A change of model owner is ratified by the committee, after the fact.

Who owns a model is who answers for it, so the appointment is the MRC's to ratify.
But the record cannot sit ownerless while a committee finds a date: the new owner
takes the model straight away, the console says the sign-off is outstanding, and the
request carries both names so the committee ratifies a change rather than a fact it
cannot check.
"""
from __future__ import annotations

from src.web._owner_ratification import pending_owner_request
from tests.web._signoff_flows import (_register_subject_model, _schedule_meeting,
                                      _seed_mrc, _signoff_agenda_items, decide)
from tests.web.conftest import HEADERS


def _set_owner(client, owner, model_id="M1"):
    return client.post(f"/api/models/{model_id}/field",
                       json={"field": "owner", "value": owner, "confirmed": True},
                       headers=HEADERS)


def _model(client, model_id="M1"):
    return client.get(f"/api/models/{model_id}").get_json()


def _owner_items(client, meeting_id="MTG1"):
    agenda = client.get(f"/api/meetings/{meeting_id}").get_json()["data"]["agenda"]
    return [a for a in _signoff_agenda_items(agenda) if a.get("signoff_kind") == "owner"]


def test_the_new_owner_takes_the_model_at_once(client):
    """A model cannot sit unowned while a committee meets."""
    _seed_mrc(client)
    _register_subject_model(client, owner="Dee Patel")
    _set_owner(client, "Ravi Shah")
    assert _model(client)["data"]["owner"] == "Ravi Shah"


def test_the_change_raises_a_ratification_carrying_both_names(client):
    _seed_mrc(client)
    _register_subject_model(client, owner="Dee Patel")
    _set_owner(client, "Ravi Shah")

    request = pending_owner_request(_model(client)["data"])
    assert request is not None
    assert (request["from_owner"], request["to_owner"]) == ("Dee Patel", "Ravi Shah")
    assert request["kind"] == "owner"


def test_it_reaches_the_committee_as_its_own_agenda_item(client):
    _seed_mrc(client)
    _register_subject_model(client, owner="Dee Patel")
    _schedule_meeting(client)
    _set_owner(client, "Ravi Shah")

    items = _owner_items(client)
    assert len(items) == 1
    assert "Model owner" in items[0]["title"]
    assert "Dee Patel" in items[0]["title"] and "Ravi Shah" in items[0]["title"]
    assert (items[0]["from_owner"], items[0]["to_owner"]) == ("Dee Patel", "Ravi Shah")


def test_ratifying_records_who_handed_the_model_to_whom(client):
    _seed_mrc(client)
    _register_subject_model(client, owner="Dee Patel")
    _schedule_meeting(client)
    _set_owner(client, "Ravi Shah")
    decide(client, _owner_items(client)[0]["item_id"])

    data = _model(client)["data"]
    entry = next(h for h in data["signoff_history"] if h["kind"] == "owner")
    assert entry["outcome"] == "Approved"
    assert (entry["from_owner"], entry["to_owner"]) == ("Dee Patel", "Ravi Shah")
    assert data["owner"] == "Ravi Shah"
    assert pending_owner_request(data) is None, "nothing outstanding once ratified"

    minutes = client.get("/api/meetings/MTG1").get_json()["data"]["minutes"]
    assert any("Model owner ratified" in (m.get("title") or "") for m in minutes)


def test_a_rejected_appointment_leaves_the_owner_in_place_and_says_so(client):
    """The model keeps the owner it has — somebody is answering for it either way —
    and the rejection stands on the record for the owner to resolve."""
    _seed_mrc(client)
    _register_subject_model(client, owner="Dee Patel")
    _schedule_meeting(client)
    _set_owner(client, "Ravi Shah")
    decide(client, _owner_items(client)[0]["item_id"], outcome="reject")

    data = _model(client)["data"]
    assert data["owner"] == "Ravi Shah"
    entry = next(h for h in data["signoff_history"] if h["kind"] == "owner")
    assert entry["outcome"] == "Rejected"


def test_setting_the_same_owner_again_raises_nothing(client):
    """Only a change goes to the committee; re-saving the same name is not one."""
    _seed_mrc(client)
    _register_subject_model(client, owner="Dee Patel")
    _set_owner(client, "Dee Patel")
    assert pending_owner_request(_model(client)["data"]) is None


def test_one_live_request_per_model_however_often_the_owner_moves(client):
    """Two changes before a meeting leave the committee one question, not two."""
    _seed_mrc(client)
    _register_subject_model(client, owner="Dee Patel")
    _set_owner(client, "Ravi Shah")
    _set_owner(client, "Priya Anand")

    live = [r for r in _model(client)["data"]["signoff_requests"]
            if r["kind"] == "owner" and r["status"] in ("Pending", "Attached")]
    assert len(live) == 1
    assert live[0]["to_owner"] == "Priya Anand"
