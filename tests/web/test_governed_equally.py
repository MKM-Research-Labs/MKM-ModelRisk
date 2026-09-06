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
"""A model, an ML Application and an AI System are governed identically.

Not "similarly". The same committee, reached the same way, on the same triggers. Two
differences had appeared without anyone choosing them, and both are asserted away here:

- **Routing.** An escalation ladder briefly sent mission-critical and agentic records
  to a company committee. It blocked two live tier-1 models that had routed to their
  division committee for months. Every record is managed at the MRC it is assigned to
  — the MRC is the risk committee, and it is itself the escalation point.
- **Ownership.** A change of model owner went to the committee to be ratified; a change
  of ML Application or AI System owner went to nobody.
"""
from __future__ import annotations

import pytest

from tests.web._signoff_flows import _seed_mrc
from tests.web.conftest import HEADERS

_SUBJECTS = {
    "model": {"api": "/api/models", "id_key": "model_id", "id": "M-EQ-1",
              "top_level": {"name": "Alpha"},
              "fields": {"division": "Risk", "owner": "David K Kelly"}},
    "ml_application": {"api": "/api/ml-applications", "id_key": "ml_application_id",
                       "id": "MLA-EQ-1",
                       "fields": {"name": "Retail PD scorecard", "division": "Risk",
                                  "owner": "David K Kelly",
                                  "estimator": "GradientBoostingClassifier",
                                  "use_case": "Ranks retail applicants."}},
    "ai_system": {"api": "/api/ai-systems", "id_key": "ai_system_id", "id": "AIS-EQ-1",
                  "fields": {"name": "Client mail summariser", "division": "Risk",
                             "owner": "David K Kelly",
                             "use_case": "Summarises inbound client correspondence.",
                             "deployment_pattern": "Agentic (tool-using)"}},
}
_KINDS = sorted(_SUBJECTS)


def _register(client, kind, **overrides):
    """Registered under a division that has a committee.

    Seeded here rather than assumed: routing resolves against the committees the
    institution has actually defined, so a test with none would prove that a record
    routes nowhere — which is true, and not what is being asserted.
    """
    _seed_mrc(client, value="MRC-DIV", level="Division", scope_value="Risk")
    cfg = _SUBJECTS[kind]
    payload = {cfg["id_key"]: cfg["id"], "fields": {**cfg["fields"], **overrides},
               "confirmed": True, **cfg.get("top_level", {})}
    return client.post(cfg["api"], json=payload, headers=HEADERS)


def _mrc(client, kind):
    cfg = _SUBJECTS[kind]
    return client.get(f"{cfg['api']}/{cfg['id']}/mrc", headers=HEADERS).get_json()


def _data(client, kind):
    cfg = _SUBJECTS[kind]
    return client.get(f"{cfg['api']}/{cfg['id']}",
                      headers=HEADERS).get_json()["data"]


# --- Every record is managed at the MRC it is assigned to ---------------------

@pytest.mark.parametrize("kind", _KINDS)
def test_a_record_routes_to_the_committee_covering_its_org_location(client, kind):
    _register(client, kind)
    outcome = _mrc(client, kind)
    assert outcome["blocked"] is False
    assert outcome["mrc"], f"{kind} routed nowhere"


@pytest.mark.parametrize("kind", _KINDS)
def test_being_mission_critical_does_not_send_a_record_somewhere_else(client, kind):
    """Tier 1 is how serious a record is, not which committee it belongs to. This is
    the rule that blocked MKM-GH-001 and MKM-PR-001 — both tier-1 models that had
    routed to the PhysicalRisk Division MRC for months."""
    # A model's tier is stored as an integer and the two newer types keep a string.
    # That is a field-type difference, not a governance one — the point of the test is
    # that being tier 1 does not change WHICH committee governs the record.
    tier = 1 if kind == "model" else "1"
    _register(client, kind, tier=tier, materiality="High")
    outcome = _mrc(client, kind)
    assert outcome["blocked"] is False
    assert outcome["mrc"], f"tier-1 {kind} routed nowhere"


def test_an_agentic_ai_system_routes_like_everything_else(client):
    """What a system can DO does not change which committee governs it. It is used in
    a division, so the division's committee covers it."""
    _register(client, "ai_system", deployment_pattern="Agentic (tool-using)")
    agentic = _mrc(client, "ai_system")
    assert agentic["blocked"] is False
    assert agentic["mrc"]


def test_the_three_record_types_reach_the_same_committee(client):
    """Same division, same line of business, same committee — whatever the record is."""
    for kind in _KINDS:
        _register(client, kind)
    reached = {kind: (_mrc(client, kind)["mrc"] or {}).get("value") for kind in _KINDS}
    assert len(set(reached.values())) == 1, f"they disagreed: {reached}"


# --- The same sign-off triggers ----------------------------------------------

@pytest.mark.parametrize("kind", _KINDS)
def test_changing_the_owner_is_ratified_by_the_committee(client, kind):
    """Who owns a record is who answers for it, so the appointment is the committee's
    to ratify. The new owner takes the record straight away — it cannot sit ownerless —
    and the ratification follows, carrying both names so the committee ratifies a
    change rather than a fact it cannot check."""
    cfg = _SUBJECTS[kind]
    _register(client, kind)
    client.post(f"{cfg['api']}/{cfg['id']}/field",
                json={"field": "owner", "value": "Tom Cairney", "confirmed": True},
                headers=HEADERS)
    data = _data(client, kind)
    assert data["owner"] == "Tom Cairney", "the new owner should take the record at once"
    owner_requests = [r for r in data.get("signoff_requests") or []
                      if r.get("kind") == "owner"]
    assert owner_requests, f"{kind} changed owner without telling the committee"
    assert owner_requests[-1]["from_owner"] == "David K Kelly"
    assert owner_requests[-1]["to_owner"] == "Tom Cairney"


@pytest.mark.parametrize("kind", _KINDS)
def test_editing_something_that_is_not_the_owner_raises_nothing(client, kind):
    """The trigger is the appointment, not every edit. A record that queued a
    ratification for each field change would train people to ignore them."""
    cfg = _SUBJECTS[kind]
    _register(client, kind)
    client.post(f"{cfg['api']}/{cfg['id']}/field",
                json={"field": "line_of_business", "value": "PRS Platform",
                      "confirmed": True}, headers=HEADERS)
    data = _data(client, kind)
    assert not [r for r in data.get("signoff_requests") or [] if r.get("kind") == "owner"]
