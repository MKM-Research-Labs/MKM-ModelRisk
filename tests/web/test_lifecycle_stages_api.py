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
"""The lifecycle stage API: the registry every screen resolves against, and the two
ratification journeys behind it.

The registry is the piece worth testing hardest. It hands back the stages **already
resolved per division** -- the whole catalogue where a division has ratified nothing,
its own ordered choice where it has -- so that the "empty means everything" rule is not
re-implemented in JavaScript and cannot drift from the domain's.
"""
from __future__ import annotations

from config.governance import VALID_LIFECYCLE_STAGES
from src.governance.reference import add_option
from tests.web.conftest import HEADERS

DIV = "PhysicalRisk"


def _division(client, name=DIV):
    add_option(list_name="division", fields={"value": name}, actor="admin")


def _catalogue(client, stages, approve=True):
    res = client.post("/api/lifecycle-catalogue/propose",
                      json={"stages": stages, "confirmed": True}, headers=HEADERS)
    if approve:
        client.post("/api/lifecycle-catalogue/approve",
                    json={"meeting_id": "MRC-1", "confirmed": True}, headers=HEADERS)
    return res


def _shipped(**overrides):
    return [{"value": v, "label": overrides.get(v, v)} for v in VALID_LIFECYCLE_STAGES]


def test_the_registry_offers_the_catalogue_where_nothing_is_narrowed(client):
    _division(client)
    registry = client.get("/api/lifecycle-stages").get_json()
    assert [s["value"] for s in registry["catalogue"]] == list(VALID_LIFECYCLE_STAGES)
    assert registry["divisions"][DIV] == list(VALID_LIFECYCLE_STAGES)
    assert registry["catalogue_state"] == "seed"
    assert registry["states"][DIV]["state"] == "seed"


def test_the_registry_carries_the_label_for_every_stored_value(client):
    _division(client)
    _catalogue(client, _shipped(Production="Live in production"))
    registry = client.get("/api/lifecycle-stages").get_json()
    assert registry["labels"][DIV]["Production"] == "Live in production"


def test_a_division_narrows_and_the_registry_follows(client):
    _division(client)
    client.post(f"/api/lifecycle-stages/{DIV}/propose",
                json={"stages": ["Development", "Production"], "confirmed": True},
                headers=HEADERS)
    assert client.get("/api/lifecycle-stages").get_json()["divisions"][DIV] \
        == list(VALID_LIFECYCLE_STAGES), "a draft changes nothing"

    client.post(f"/api/lifecycle-stages/{DIV}/approve",
                json={"meeting_id": "MRC-1", "confirmed": True}, headers=HEADERS)
    assert client.get("/api/lifecycle-stages").get_json()["divisions"][DIV] \
        == ["Development", "Production"]


def test_the_division_detail_separates_what_was_chosen_from_what_it_resolves_to(client):
    _division(client)
    detail = client.get(f"/api/lifecycle-stages/{DIV}").get_json()
    assert detail["chosen"] == [], "nothing ratified"
    assert detail["stages"] == list(VALID_LIFECYCLE_STAGES), "which means everything"
    assert detail["state"] == "seed"


def test_the_catalogue_detail_counts_what_is_in_each_stage(client):
    client.post("/api/models", json={"model_id": "M1", "name": "Alpha",
                                     "confirmed": True,
                                     "fields": {"lifecycle_stage": "Production"}},
                headers=HEADERS)
    detail = client.get("/api/lifecycle-catalogue").get_json()
    assert detail["in_use"] == {"Production": 1}
    assert detail["state"] == "seed"


def test_a_catalogue_draft_reaches_the_committee_and_drives_nothing_before_it(client):
    _division(client)
    res = _catalogue(client, _shipped() + [{"value": "Decommissioning",
                                            "label": "Winding down"}], approve=False)
    assert res.status_code == 201
    assert client.get("/api/lifecycle-catalogue").get_json()["state"] == "draft"
    assert "Decommissioning" not in \
        client.get("/api/lifecycle-stages").get_json()["divisions"][DIV]

    client.post("/api/lifecycle-catalogue/approve",
                json={"meeting_id": "MRC-1", "confirmed": True}, headers=HEADERS)
    assert "Decommissioning" in \
        client.get("/api/lifecycle-stages").get_json()["divisions"][DIV]


def test_rejecting_a_catalogue_draft_leaves_the_catalogue_standing(client):
    _catalogue(client, _shipped(Production="Live"), approve=False)
    client.post("/api/lifecycle-catalogue/reject",
                json={"meeting_id": "MRC-1", "confirmed": True}, headers=HEADERS)
    detail = client.get("/api/lifecycle-catalogue").get_json()
    assert detail["state"] == "seed" and detail["draft"] is None


def test_a_stage_records_are_in_cannot_be_dropped_through_the_api(client):
    _division(client)
    client.post("/api/models", json={"model_id": "M2", "name": "Beta", "confirmed": True,
                                     "fields": {"division": DIV,
                                                "lifecycle_stage": "Production"}},
                headers=HEADERS)
    dropped = _catalogue(client, [s for s in _shipped() if s["value"] != "Production"],
                         approve=False)
    assert dropped.status_code == 400
    assert "M2" in dropped.get_json()["error"], "the refusal names what is in the way"


def test_a_division_cannot_coin_a_stage_through_the_api(client):
    """Kept apart from the removal case above rather than combined: a proposal that
    both coins a stage and drops one in use hits whichever check runs first, and
    asserting that order would be asserting something nobody chose."""
    _division(client)
    coined = client.post(f"/api/lifecycle-stages/{DIV}/propose",
                         json={"stages": ["Nonsense"], "confirmed": True},
                         headers=HEADERS)
    assert coined.status_code == 400
    assert "not in the institution's lifecycle stage catalogue" in \
        coined.get_json()["error"]


def test_the_catalogue_is_not_reachable_as_a_division(client):
    """It sits on its own path: a division named "catalogue" would otherwise shadow the
    committee's own endpoint, or be shadowed by it."""
    assert client.get("/api/lifecycle-catalogue").status_code == 200
    assert "chosen" not in client.get("/api/lifecycle-catalogue").get_json()


def test_the_catalogue_says_when_no_committee_can_ratify_it(client):
    """A draft nobody can sign off is worse than no draft: it looks saved and goes
    nowhere. The catalogue is firm-wide, so only a Company-level committee may ratify
    it — and an estate whose only committee sits at Division level has none, which is
    a real configuration and is what the MKM estate has."""
    assert client.get("/api/lifecycle-catalogue").get_json()["ratifier"] is None

    add_option(list_name="mrc", fields={"value": "MRC-DIV", "name": "PhysicalRisk MRC",
                                        "level": "Division", "scope_value": DIV},
               actor="admin")
    assert client.get("/api/lifecycle-catalogue").get_json()["ratifier"] is None, \
        "a division committee is not entitled to ratify a firm-wide catalogue"

    add_option(list_name="mrc", fields={"value": "MRC-CO", "name": "Group MRC",
                                        "level": "Company"}, actor="admin")
    assert client.get("/api/lifecycle-catalogue").get_json()["ratifier"] == "MRC-CO"
