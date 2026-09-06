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
"""What an AI System's owner can record while it is running — over HTTP.

The three Phase 3–5 capabilities that had no way in. ``record_variability_envelope``,
``set_trigger_threshold`` and ``seal_release_manifest`` were built, tested at the
domain level, and reachable by nothing: no route, no ingest endpoint, no button. The
envelope panel could only ever read "not measured", which is the most flattering
reading of the least evidence — exactly what the envelope exists to prevent.

These tests are about the seam, not the arithmetic: that the refusals the domain
makes actually reach a caller, and that what is recorded comes back on the record.
"""
from __future__ import annotations

from config.governance._ai_baseline import (ENVELOPE_OK, ENVELOPE_STALE,
                                            MIN_ENVELOPE_RUNS)
from config.governance._ai_triggers import FALLBACK_STATES, TRIGGER_PROPERTIES
from tests.web.conftest import HEADERS

_MINIMUM = {"name": "Client mail summariser", "division": "Risk",
            "owner": "David K Kelly",
            "use_case": "Summarises inbound client correspondence for the desk.",
            "deployment_pattern": "Agentic (tool-using)"}
_ID = "AIS-OP-1"
_ENOUGH = [0.70 + (i % 7) * 0.01 for i in range(MIN_ENVELOPE_RUNS + 4)]


def _register(client, ai_system_id=_ID, **overrides):
    return client.post("/api/ai-systems", json={
        "ai_system_id": ai_system_id, "fields": {**_MINIMUM, **overrides},
        "confirmed": True}, headers=HEADERS)


def _ready(client, ai_system_id=_ID, **overrides):
    """Registered, with a configuration snapshot taken.

    The snapshot is not ceremony: an envelope has to say which configuration it was
    measured under, and the domain refuses one that cannot. That ordering is itself
    worth stating, so it is asserted below rather than only relied on here.
    """
    _register(client, ai_system_id, **overrides)
    client.post(f"/api/ai-systems/{ai_system_id}/snapshots",
                json={"confirmed": True}, headers=HEADERS)


def _data(client, ai_system_id=_ID):
    return client.get(f"/api/ai-systems/{ai_system_id}",
                      headers=HEADERS).get_json()["data"]


# --- The variability envelope -------------------------------------------------

def test_an_envelope_from_too_few_runs_is_refused_rather_than_narrowed(client):
    """The dangerous failure is the flattering one: three runs that happen to agree
    produce a tight range that reads like a well-behaved system."""
    _ready(client)
    res = client.post(f"/api/ai-systems/{_ID}/envelope",
                      json={"scores": [0.71, 0.68, 0.75], "confirmed": True},
                      headers=HEADERS)
    assert res.status_code == 400
    assert str(MIN_ENVELOPE_RUNS) in res.get_json()["error"]


def test_enough_runs_state_an_envelope_and_it_reads_back(client):
    _ready(client)
    posted = client.post(f"/api/ai-systems/{_ID}/envelope",
                         json={"scores": _ENOUGH, "confirmed": True},
                         headers=HEADERS)
    assert posted.status_code == 201
    assert posted.get_json()["envelope"]["status"] == ENVELOPE_OK
    read = client.get(f"/api/ai-systems/{_ID}/envelope", headers=HEADERS).get_json()
    assert read["envelope"]["status"] == ENVELOPE_OK
    assert read["envelope"]["runs"] == len(_ENOUGH)


def test_an_envelope_goes_stale_when_the_configuration_moves_under_it(client):
    """Not deleted — it is the record of what was measured. Stale is a finding; a
    missing envelope is a gap, and the two must not read alike."""
    _ready(client)
    client.post(f"/api/ai-systems/{_ID}/envelope",
                json={"scores": _ENOUGH, "confirmed": True}, headers=HEADERS)
    # A CONFIGURATION field, not a governance one. The test of what belongs in a
    # snapshot is reproducibility: changing the guardrails could make the same input
    # give a different answer, so it moves the version. Changing the owner could not,
    # and does not — which is the distinction this assertion is really about.
    client.post(f"/api/ai-systems/{_ID}/field",
                json={"field": "guardrails", "value": "Output filter added.",
                      "confirmed": True}, headers=HEADERS)
    client.post(f"/api/ai-systems/{_ID}/snapshots", json={"confirmed": True},
                headers=HEADERS)
    read = client.get(f"/api/ai-systems/{_ID}/envelope", headers=HEADERS).get_json()
    assert read["envelope"]["status"] == ENVELOPE_STALE


def test_an_envelope_needs_a_configuration_to_be_measured_under(client):
    """Refused before the arithmetic is even attempted. An envelope with no
    configuration behind it is a number nobody can reproduce."""
    _register(client)
    res = client.post(f"/api/ai-systems/{_ID}/envelope",
                      json={"scores": _ENOUGH, "confirmed": True}, headers=HEADERS)
    assert res.status_code == 400
    assert "snapshot" in res.get_json()["error"]


def test_recording_an_envelope_against_nothing_is_404(client):
    res = client.post("/api/ai-systems/AIS-NOPE/envelope",
                      json={"scores": _ENOUGH, "confirmed": True}, headers=HEADERS)
    assert res.status_code == 404


# --- Trigger thresholds -------------------------------------------------------

def test_a_threshold_on_something_that_is_not_a_trigger_property_is_refused(client):
    """"tone" is a dimension the ACE scores, not a property a trigger fires on. A
    number set against it would look configured and never fire."""
    _register(client)
    res = client.post(f"/api/ai-systems/{_ID}/thresholds",
                      json={"property_name": "tone", "threshold": 0.5,
                            "fallback": FALLBACK_STATES[0], "confirmed": True},
                      headers=HEADERS)
    assert res.status_code == 400
    assert "not a trigger property" in res.get_json()["error"]


def test_a_threshold_is_set_and_carries_its_fallback(client):
    _register(client)
    prop = TRIGGER_PROPERTIES[0]
    res = client.post(f"/api/ai-systems/{_ID}/thresholds",
                      json={"property_name": prop, "threshold": 0.9,
                            "fallback": FALLBACK_STATES[2],
                            "rationale": "Below this the summary misstates the mail.",
                            "confirmed": True}, headers=HEADERS)
    assert res.status_code == 201
    held = _data(client)["trigger_thresholds"][prop]
    assert held["threshold"] == 0.9
    assert held["fallback"] == FALLBACK_STATES[2]


def test_setting_one_threshold_leaves_the_others_alone(client):
    """One event per property, never a set of four — otherwise "we tightened
    correctness" is indistinguishable from "we restated all four"."""
    _register(client)
    first, second = TRIGGER_PROPERTIES[0], TRIGGER_PROPERTIES[1]
    for prop, bar in ((first, 0.9), (second, 0.8)):
        client.post(f"/api/ai-systems/{_ID}/thresholds",
                    json={"property_name": prop, "threshold": bar,
                          "fallback": FALLBACK_STATES[0], "confirmed": True},
                    headers=HEADERS)
    held = _data(client)["trigger_thresholds"]
    assert held[first]["threshold"] == 0.9
    assert held[second]["threshold"] == 0.8


# --- The release manifest -----------------------------------------------------

def test_a_release_needs_a_name(client):
    _register(client)
    res = client.post(f"/api/ai-systems/{_ID}/release-manifest",
                      json={"release": "   ", "change_class": "Bounded",
                            "confirmed": True}, headers=HEADERS)
    assert res.status_code == 400
    assert "needs a name" in res.get_json()["error"]


def test_a_sealed_manifest_appears_on_the_record(client):
    _ready(client)
    res = client.post(f"/api/ai-systems/{_ID}/release-manifest",
                      json={"release": "2026.09.1", "change_class": "Bounded",
                            "note": "Prompt revision.", "confirmed": True},
                      headers=HEADERS)
    assert res.status_code == 201
    manifests = _data(client)["release_manifests"]
    assert [m["release"] for m in manifests] == ["2026.09.1"]
    assert manifests[0]["change_class"] == "Bounded"


def test_a_release_is_sealed_once_and_not_again(client):
    """Sealed, not saved. A manifest is the statement of what was released; a second
    seal under the same name would make the first one a draft."""
    _ready(client)
    body = {"release": "2026.09.1", "change_class": "Bounded", "confirmed": True}
    assert client.post(f"/api/ai-systems/{_ID}/release-manifest", json=body,
                       headers=HEADERS).status_code == 201
    again = client.post(f"/api/ai-systems/{_ID}/release-manifest", json=body,
                        headers=HEADERS)
    assert again.status_code == 400
    assert "already sealed" in again.get_json()["error"]


def test_a_governance_edit_does_not_stale_an_envelope(client):
    """The other side of the same rule. Changing who owns a system cannot change what
    it answers, so an envelope measured before that edit still describes it. An
    envelope that went stale on every edit would be ignored within a week."""
    _ready(client)
    client.post(f"/api/ai-systems/{_ID}/envelope",
                json={"scores": _ENOUGH, "confirmed": True}, headers=HEADERS)
    client.post(f"/api/ai-systems/{_ID}/field",
                json={"field": "owner", "value": "Tom Cairney", "confirmed": True},
                headers=HEADERS)
    client.post(f"/api/ai-systems/{_ID}/snapshots", json={"confirmed": True},
                headers=HEADERS)
    read = client.get(f"/api/ai-systems/{_ID}/envelope", headers=HEADERS).get_json()
    assert read["envelope"]["status"] == ENVELOPE_OK
