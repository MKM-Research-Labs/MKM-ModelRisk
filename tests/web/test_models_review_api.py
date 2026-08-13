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
"""The review workflow's interim approvals."""
from __future__ import annotations

from tests.web.conftest import HEADERS


def _register(client, model_id="M1"):
    return client.post(
        "/api/models",
        json={"model_id": model_id, "name": "Alpha", "fields": {}, "confirmed": True},
        headers=HEADERS,
    )


def _approve(client, stage, note="", model_id="M1"):
    return client.post(
        f"/api/models/{model_id}/review/approve-stage",
        json={"stage": stage, "note": note, "confirmed": True}, headers=HEADERS,
    )


def test_interim_approval_records_who_agreed_and_moves_the_status(client):
    """The reviewer agrees a stage; the model's review status follows from the work
    done rather than from somebody remembering to change a dropdown."""
    _register(client)
    data = _approve(client, "documents", note="Pack complete").get_json()["data"]
    assert data["review_status"] == "Documents reviewed"
    row = data["review_progress"][0]
    assert row["stage"] == "documents"
    assert row["stage_label"] == "Preliminary documents"
    assert row["note"] == "Pack complete"
    assert row["approved_by"] == HEADERS["X-Auth-Request-User"]
    assert row["approved_at"]


def test_each_stage_carries_the_status_forward(client):
    _register(client)
    for stage, status in (("documents", "Documents reviewed"),
                          ("questions", "Questions answered"),
                          ("weaknesses", "Weaknesses agreed"),
                          ("limitations", "Limitations agreed"),
                          ("monitoring", "Monitoring agreed")):
        assert _approve(client, stage).get_json()["data"]["review_status"] == status


def test_reapproving_a_reopened_stage_appends_rather_than_replaces(client):
    """A stage reopened and re-agreed leaves both approvals standing: the register
    is the record of how the review actually went, not a tidy summary of it."""
    _register(client)
    _approve(client, "questions", note="First pass")
    data = _approve(client, "questions", note="After the rework").get_json()["data"]
    notes = [r["note"] for r in data["review_progress"] if r["stage"] == "questions"]
    assert notes == ["First pass", "After the rework"]


def test_unknown_stage_is_400(client):
    _register(client)
    assert _approve(client, "bogus").status_code == 400


def test_approval_requires_confirmation(client):
    """Agreeing a stage names a person as having agreed it, so it goes through the
    same confirm-to-amend gate as every other amendment (409, as the policy does)."""
    _register(client)
    response = client.post(
        "/api/models/M1/review/approve-stage", json={"stage": "documents"}, headers=HEADERS,
    )
    assert response.status_code == 409
    assert response.get_json()["needs_confirmation"] is True


def test_approval_on_unknown_model_is_404(client):
    assert _approve(client, "documents", model_id="NOPE").status_code == 404


def _verdict(client, item_id, verdict, comment="", model_id="M1"):
    return client.post(
        f"/api/models/{model_id}/review/question-verdict",
        json={"item_id": item_id, "verdict": verdict, "comment": comment}, headers=HEADERS,
    )


def _first_question(client, model_id="M1"):
    model = client.get(f"/api/models/{model_id}").get_json()
    return model["data"]["validation_questions"][0]["item_id"]


def test_reviewer_verdict_is_stamped_with_who_and_when(client):
    """Who reviewed a question is stamped from the signed-in identity, never sent by
    the console: an attribution the browser supplies is not evidence of anything."""
    _register(client)
    item_id = _first_question(client)
    data = _verdict(client, item_id, "Challenged", "Benchmark is not comparable").get_json()["data"]
    row = next(q for q in data["validation_questions"] if q["item_id"] == item_id)
    assert row["reviewer_verdict"] == "Challenged"
    assert row["reviewer_comment"] == "Benchmark is not comparable"
    assert row["reviewed_by"] == HEADERS["X-Auth-Request-User"]
    assert row["reviewed_at"]


def test_owner_status_and_reviewer_verdict_are_kept_apart(client):
    """A question can be Addressed by its owner and Challenged by its reviewer at the
    same time — the disagreement is the review doing its job, and the record holds it."""
    _register(client)
    item_id = _first_question(client)
    client.post(
        f"/api/models/M1/collections/validation_questions/{item_id}",
        json={"fields": {"status": "Addressed"}, "confirmed": True}, headers=HEADERS,
    )
    data = _verdict(client, item_id, "Challenged").get_json()["data"]
    row = next(q for q in data["validation_questions"] if q["item_id"] == item_id)
    assert (row["status"], row["reviewer_verdict"]) == ("Addressed", "Challenged")


def test_unknown_verdict_is_400(client):
    _register(client)
    assert _verdict(client, _first_question(client), "Sort of").status_code == 400


def test_verdict_on_unknown_model_is_404(client):
    assert _verdict(client, "VQ-001", "Accepted", model_id="NOPE").status_code == 404
