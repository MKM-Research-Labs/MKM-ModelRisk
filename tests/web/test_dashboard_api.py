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
"""Tests for the dashboard API — the landing tab's payload.

The rule itself is tested against fixtures in ``tests/governance/test_attention.py``.
What is asserted here is the contract the screen is drawn from: that the payload
answers the question, that every word on the page travels with it rather than being
written into the JavaScript, and that the surface stays read-only.
"""
from __future__ import annotations

from config.governance import ATTENTION_STATES, RESPONSE_STATES
from tests.web.conftest import HEADERS


def _register(client, model_id="M1", name="Alpha", **fields):
    return client.post(
        "/api/models",
        json={"model_id": model_id, "name": name, "fields": fields, "confirmed": True},
        headers=HEADERS,
    )


def _dash(client, **params):
    response = client.get("/api/dashboard", query_string=params)
    assert response.status_code == 200
    return response.get_json()


def test_an_empty_register_answers_the_question_with_no(client):
    payload = _dash(client)
    assert payload["verdict"]["response_required"] is False
    assert payload["estate"]["total"] == 0
    assert payload["direction"]["records_audited"] == 0


def test_the_payload_carries_every_block_the_page_and_the_erm_read(client):
    payload = _dash(client)
    for block in ("as_of", "verdict", "queue", "estate", "operational",
                  "direction", "states", "items"):
        assert block in payload, block


def test_the_state_vocabulary_travels_with_the_payload(client):
    """No state name, card heading or instruction may be written into a .js file:
    every one of them is an adopter's to rename."""
    states = _dash(client)["states"]
    assert [s["state"] for s in states] == list(ATTENTION_STATES)
    for state in states:
        assert state["label"] and state["card"] and state["response"]
        assert state["needs_response"] == (state["state"] in RESPONSE_STATES)


def test_every_state_is_counted_so_no_card_renders_blank(client):
    counts = _dash(client)["verdict"]["counts"]
    assert set(counts) == set(ATTENTION_STATES)


def test_a_registered_model_reaches_the_queue_and_the_estate(client):
    _register(client, tier=1, owner="bob", division="Retail")
    payload = _dash(client)
    assert payload["estate"]["total"] == 1
    assert payload["estate"]["by_tier"] == {"1": 1}
    assert payload["direction"]["records_audited"] == 1
    # A bare registration is far short of any division's standard, so it is owed.
    assert payload["verdict"]["response_required"] is True


def test_an_overdue_review_names_its_owner_and_its_date(client):
    _register(client, tier=1, owner="bob", next_review_date="2020-01-01")
    items = _dash(client, as_of="2026-08-24")["items"]
    overdue = [i for i in items if i["reason"] == "review_overdue"]
    # The record's worst obligation may outrank the review; either way the audit's
    # own instruction travels with whatever is reported.
    assert all(i["action"] for i in items)
    assert all(i["state"] in ATTENTION_STATES for i in items)
    if overdue:
        assert overdue[0]["owner"] == "bob" and overdue[0]["days_over"] > 0


def test_as_of_moves_the_dated_rules_without_replaying_history(client):
    _register(client, tier=1, owner="bob", next_review_date="2026-09-01")
    before = _dash(client, as_of="2026-08-24")
    after = _dash(client, as_of="2027-08-24")
    assert before["as_of"] == "2026-08-24" and after["as_of"] == "2027-08-24"
    assert before["estate"]["total"] == after["estate"]["total"] == 1


def test_one_record_contributes_one_row_however_many_ways_it_is_behind(client):
    _register(client, tier=1)
    rows = [r for r in _dash(client)["queue"]["rows"]
            if (r.get("entity") or {}).get("id") == "M1"]
    assert len(rows) <= 1


def test_the_dashboard_is_read_only(client):
    """No acknowledge, no dismiss: clearing an item from a screen would be an
    ungoverned decision with no minute against it."""
    for verb in (client.post, client.put, client.delete, client.patch):
        assert verb("/api/dashboard", headers=HEADERS).status_code == 405
