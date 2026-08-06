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
