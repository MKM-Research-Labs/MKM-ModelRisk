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
from config.governance._assessments import ADVERSE_FAIRNESS_VERDICT
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
