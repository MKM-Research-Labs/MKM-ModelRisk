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
"""The fairness gate at the review sign-off, on every governed record type.

The point of these is the last two: a review that was ready to sign becomes unsignable
the moment a disparity is recorded, and becomes signable again only when the attribute
is assessed afresh. Everything before them is the setup that makes those two mean
something.
"""
from __future__ import annotations

from config.governance import REVIEW_STAGES
from config.governance._ai_system_collections import AI_SYSTEM_COLLECTION_SPECS
from config.governance._assessments import (ADVERSE_EVALUATION_VERDICT,
                                             ADVERSE_FAIRNESS_VERDICT,
                                             EVALUATIONS_COLLECTION)
from tests.web.conftest import HEADERS

_AI = {"name": "Claims triage agent", "division": "Risk", "owner": "David K Kelly",
       "use_case": "Triages inbound property claims.",
       "deployment_pattern": "Agentic (tool-using)"}


def _register(client):
    client.post("/api/ai-systems", json={"ai_system_id": "AIS-0001", "fields": _AI,
                                         "actor": "admin"}, headers=HEADERS)


def _agree_every_stage(client):
    for stage in REVIEW_STAGES:
        client.post("/api/ai-systems/AIS-0001/review/approve-stage",
                    json={"stage": stage["key"], "confirmed": True}, headers=HEADERS)


def _blockers(client):
    return client.get("/api/ai-systems/AIS-0001/review/blockers").get_json()["blockers"]


def _add_fairness(client, attribute, verdict):
    return client.post(
        "/api/ai-systems/AIS-0001/collections/fairness_assessments",
        json={"fields": {"attribute": attribute, "verdict": verdict},
              "confirmed": True}, headers=HEADERS)


def _sign_off(client):
    return client.post("/api/ai-systems/AIS-0001/review/sign-off",
                       json={"commentary": "Reviewed and accepted.", "confirmed": True},
                       headers=HEADERS)


def test_a_review_with_every_stage_agreed_is_ready_to_sign(client):
    _register(client)
    _agree_every_stage(client)
    assert _blockers(client) == []


def test_a_measured_disparity_blocks_the_sign_off(client):
    _register(client)
    _agree_every_stage(client)
    _add_fairness(client, "Age band", ADVERSE_FAIRNESS_VERDICT)

    assert _blockers(client) == ["1 unanswered fairness finding (Age band)"]
    refused = _sign_off(client)
    assert refused.status_code == 400
    assert "Age band" in refused.get_json()["error"]


def test_assessing_the_attribute_again_answers_it(client):
    """Answered by a fresh assessment saying what changed — never by editing the
    original, which would leave no record that a disparity had been found at all."""
    _register(client)
    _agree_every_stage(client)
    _add_fairness(client, "Age band", ADVERSE_FAIRNESS_VERDICT)
    _add_fairness(client, "Age band", "Within tolerance")

    assert _blockers(client) == []
    assert _sign_off(client).status_code == 201


def test_a_finding_on_another_attribute_still_blocks(client):
    _register(client)
    _agree_every_stage(client)
    _add_fairness(client, "Age band", ADVERSE_FAIRNESS_VERDICT)
    _add_fairness(client, "Postcode", "No disparity found")

    assert _blockers(client) == ["1 unanswered fairness finding (Age band)"]


def test_an_assessment_with_no_verdict_does_not_block(client):
    """Every fairness row in the estate predates the verdict field."""
    _register(client)
    _agree_every_stage(client)
    client.post("/api/ai-systems/AIS-0001/collections/fairness_assessments",
                json={"fields": {"attribute": "Age band",
                                 "finding": "Looked at it; nothing conclusive."},
                      "confirmed": True}, headers=HEADERS)
    assert _blockers(client) == []


# --- The evaluations half of the same gate ------------------------------------
#
# Fairness findings were tested here and failed evaluations were not, though they
# block on identical reasoning: an evaluation whose most recent run failed is
# answered by running that kind again and recording what changed, not by signing
# past it.

# The kinds are an adopter-renameable vocabulary, so they are read rather than typed:
# a test asserting "Red team" breaks on an institution that words its own list.
_KINDS = [f["options"] for f in AI_SYSTEM_COLLECTION_SPECS[EVALUATIONS_COLLECTION]["fields"]
          if f["key"] == "kind"][0]
_RED_TEAM, _OTHER_KIND = _KINDS[2], _KINDS[0]


def _add_evaluation(client, kind, passed):
    return client.post(
        "/api/ai-systems/AIS-0001/collections/evaluations",
        json={"fields": {"kind": kind, "passed": passed}, "confirmed": True},
        headers=HEADERS)


def test_a_failed_evaluation_blocks_the_sign_off(client):
    _register(client)
    _agree_every_stage(client)
    _add_evaluation(client, _RED_TEAM, ADVERSE_EVALUATION_VERDICT)
    blockers = _blockers(client)
    assert any("failed evaluation" in b for b in blockers), blockers
    # The blocker names the kind, so the reviewer knows which exercise to re-run
    # rather than being told a count and left to hunt.
    assert any(_RED_TEAM in b for b in blockers), blockers
    assert _sign_off(client).status_code >= 400


def test_running_that_kind_again_and_passing_answers_it(client):
    """Keyed by KIND, not by row: "does this thing pass its red team" is the question,
    not "did run 14 pass". A failed red team answered by a later passing one is
    answered."""
    _register(client)
    _agree_every_stage(client)
    _add_evaluation(client, _RED_TEAM, ADVERSE_EVALUATION_VERDICT)
    _add_evaluation(client, _RED_TEAM, "Passed")
    assert not any("failed evaluation" in b for b in _blockers(client))
    assert _sign_off(client).status_code in (200, 201)


def test_a_failure_of_another_kind_still_blocks(client):
    """Passing one exercise does not answer a different one."""
    _register(client)
    _agree_every_stage(client)
    _add_evaluation(client, _RED_TEAM, ADVERSE_EVALUATION_VERDICT)
    _add_evaluation(client, _OTHER_KIND, "Passed")
    assert any("failed evaluation" in b for b in _blockers(client))

