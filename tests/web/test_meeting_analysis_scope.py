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
"""Being presented to the committee for analysis, on every governed record type.

One of the four sign-off triggers. It existed for models and products only: an ML
Application or an AI System could be rated, reviewed and signed off, but never put in
front of the committee that governs it, because only two record types had in-scope
endpoints.

The endpoints are now generated from ``MEETING_SCOPE`` rather than written per type —
three hand-written copies had already drifted, with a model's tabled paper filed onto
the record and a product's not.
"""
from __future__ import annotations

import pytest

from config.governance._mrc import VALID_ANALYSIS_STATUS
from config.governance._mrc_collections import MEETING_SCOPE
from tests.web._signoff_flows import _seed_mrc, _schedule
from tests.web.conftest import HEADERS

_RECORDS = {
    "model": {"api": "/api/models", "top_level": {"name": "Alpha"},
              "fields": {"division": "Risk", "owner": "David K Kelly"}},
    # A Product carries its name at the top level of the register payload, as a model
    # carries ``name``. The two newer record types keep theirs inside ``fields``.
    "product": {"api": "/api/products", "top_level": {"product": "Flood cover"},
                "fields": {"division": "Risk", "owner": "David K Kelly",
                           "calculating_agent": "Murex"}},
    "ml_application": {"api": "/api/ml-applications",
                       "fields": {"name": "Retail PD scorecard", "division": "Risk",
                                  "owner": "David K Kelly",
                                  "estimator": "GradientBoostingClassifier",
                                  "use_case": "Ranks retail applicants."}},
    "ai_system": {"api": "/api/ai-systems",
                  "fields": {"name": "Client mail summariser", "division": "Risk",
                             "owner": "David K Kelly",
                             "use_case": "Summarises client correspondence.",
                             "deployment_pattern": "Agentic (tool-using)"}},
}
_KINDS = sorted(_RECORDS)

# The committee's outcome vocabulary, read from config rather than typed here:
# it is an adopter-renameable list, and a test asserting "Reviewed" would break
# on an institution that words its own outcomes differently.
_REVIEWED = next(v for v in VALID_ANALYSIS_STATUS if v != "Pending")


def _rid(kind):
    return {"model": "M-SC-1", "product": "P-SC-1", "ml_application": "MLA-SC-1",
            "ai_system": "AIS-SC-1"}[kind]


def _register(client, kind):
    cfg, scope = _RECORDS[kind], MEETING_SCOPE[kind]
    payload = {scope["id_key"]: _rid(kind), "fields": cfg["fields"], "confirmed": True,
               **cfg.get("top_level", {})}
    res = client.post(cfg["api"], json=payload, headers=HEADERS)
    assert res.status_code in (200, 201), res.get_json()
    return _rid(kind)


def _meeting(client):
    _seed_mrc(client)
    _schedule(client)
    return "MTG1"


def _set_scope(client, kind, ids):
    scope = MEETING_SCOPE[kind]
    return client.post(
        f"/api/meetings/MTG1/collections/{scope['collection']}/set",
        json={f"{scope['id_key']}s": ids, "confirmed": True}, headers=HEADERS)


# --- Every record type can be put in front of its committee -------------------

def test_the_served_scope_table_covers_every_governed_record_type():
    """The console builds its Analysis sub-tabs from this. A record type missing here
    is a record type the committee has no way to look at."""
    assert set(MEETING_SCOPE) == {"model", "product", "ml_application", "ai_system"}


@pytest.mark.parametrize("kind", _KINDS)
def test_a_record_can_be_put_in_scope_for_analysis(client, kind):
    rid = _register(client, kind)
    _meeting(client)
    assert _set_scope(client, kind, [rid]).status_code == 200
    rows = client.get(f"/api/meetings/MTG1/{MEETING_SCOPE[kind]['url']}",
                      headers=HEADERS).get_json()
    assert [r[MEETING_SCOPE[kind]["id_key"]] for r in rows] == [rid]


@pytest.mark.parametrize("kind", _KINDS)
def test_the_join_carries_the_records_own_name(client, kind):
    """A Product keeps its name under ``product`` and everything else under ``name``;
    the table says which, so the meeting screen shows a name rather than an id."""
    rid = _register(client, kind)
    _meeting(client)
    _set_scope(client, kind, [rid])
    row = client.get(f"/api/meetings/MTG1/{MEETING_SCOPE[kind]['url']}",
                     headers=HEADERS).get_json()[0]
    assert row["name"], f"{kind} joined without a name"
    assert row["review_status"] is not None


@pytest.mark.parametrize("kind", _KINDS)
def test_taking_a_record_out_of_scope_removes_it(client, kind):
    """The set is diffed, and each add and remove is its own event — so the trail says
    what changed rather than that the scope was replaced."""
    rid = _register(client, kind)
    _meeting(client)
    _set_scope(client, kind, [rid])
    _set_scope(client, kind, [])
    rows = client.get(f"/api/meetings/MTG1/{MEETING_SCOPE[kind]['url']}",
                      headers=HEADERS).get_json()
    assert rows == []


@pytest.mark.parametrize("kind", _KINDS)
def test_the_committees_outcome_is_recorded_against_the_record(client, kind):
    """Outcome, note and basis-to-proceed come back on the join. Without them the
    Analysis panel re-renders "Pending" and a blank note, so saved values never appear
    to stick."""
    rid = _register(client, kind)
    _meeting(client)
    _set_scope(client, kind, [rid])
    scope = MEETING_SCOPE[kind]
    item = client.get(f"/api/meetings/MTG1/{scope['url']}",
                      headers=HEADERS).get_json()[0]
    client.post(f"/api/meetings/MTG1/collections/{scope['collection']}/{item['item_id']}",
                json={"fields": {"analysis_status": _REVIEWED,
                                 "analysis_note": "Discussed in full.",
                                 "proceed_basis": "Subject to the stated limits."},
                      "confirmed": True}, headers=HEADERS)
    row = client.get(f"/api/meetings/MTG1/{scope['url']}", headers=HEADERS).get_json()[0]
    assert row["analysis_status"] == _REVIEWED
    assert row["analysis_note"] == "Discussed in full."
    assert row["proceed_basis"] == "Subject to the stated limits."


@pytest.mark.parametrize("kind", _KINDS)
def test_tabling_a_paper_for_a_record_not_in_scope_is_refused(client, kind):
    """Named with the record type, because "record is not in scope" on a screen
    showing four kinds says nothing about which one."""
    _register(client, kind)
    _meeting(client)
    scope = MEETING_SCOPE[kind]
    res = client.post(f"/api/meetings/MTG1/{scope['url']}/{_rid(kind)}/analysis",
                      data={}, headers=HEADERS)
    assert res.status_code == 400
    assert scope["noun"] in res.get_json()["error"]
