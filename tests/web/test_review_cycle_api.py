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
"""Re-review: starting the next cycle without losing the last one.

A model is reviewed again because its owner asks, because a material version has
landed, or because the committee directed it. Starting one has to clear the board
for the new review while leaving the old one legible — the previous approvals, the
argument that produced them and the report that was signed are the history, and a
"reset" that deleted them would be destroying the evidence of the last review to
begin the next.
"""
from __future__ import annotations

import pytest

from config.governance import REVIEW_STAGES
from src.web.api_models_review import approvals, cycles
from src.governance.model_inventory import get_model
from tests.web.conftest import HEADERS


@pytest.fixture(autouse=True)
def _stub_pdf(monkeypatch):
    monkeypatch.setattr("src.governance.model_inventory.review_report.compile_tex",
                        lambda tex, assets=None: b"%PDF-review")


def _register(client):
    return client.post(
        "/api/models",
        json={"model_id": "M1", "name": "Alpha", "confirmed": True,
              "fields": {"owner": "owner@corp", "peer_reviewer": "rev@corp"}},
        headers=HEADERS,
    )


def _agree_all(client):
    for stage in REVIEW_STAGES:
        client.post("/api/models/M1/review/approve-stage",
                    json={"stage": stage["key"], "confirmed": True}, headers=HEADERS)


def _start(client, trigger="Owner change", note=""):
    return client.post("/api/models/M1/review/start-cycle",
                       json={"trigger": trigger, "note": note, "confirmed": True},
                       headers=HEADERS)


def test_starting_a_cycle_records_why(client):
    _register(client)
    data = _start(client, note="New owner wants to satisfy herself").get_json()["data"]
    assert data["review_trigger"] == "Owner change"
    assert data["review_status"] == "Not started"
    started = cycles(get_model("M1"))
    assert len(started) == 1
    assert started[0]["approved_by"] == HEADERS["X-Auth-Request-User"]
    assert started[0]["note"] == "New owner wants to satisfy herself"


def test_a_new_cycle_clears_the_board_without_erasing_the_last_review(client):
    """The stages come back outstanding, but every row that recorded the previous
    review is still there — a reset that deleted them would be destroying the
    evidence of one review in order to start the next."""
    _register(client)
    _agree_all(client)
    assert len(approvals(get_model("M1"))) == len(REVIEW_STAGES)
    before = len(get_model("M1")["data"]["review_progress"])

    _start(client, trigger="New version")
    assert approvals(get_model("M1")) == {}
    after = get_model("M1")["data"]["review_progress"]
    assert len(after) == before + 1, "the register only ever grows"

    client.post("/api/models/M1/review/approve-stage",
                json={"stage": "questions", "confirmed": True}, headers=HEADERS)
    assert list(approvals(get_model("M1"))) == ["questions"]


def test_a_signed_report_survives_the_next_cycle(client):
    _register(client)
    _agree_all(client)
    client.post("/api/models/M1/review/sign-off",
                json={"commentary": "Fit for use.", "confirmed": True}, headers=HEADERS)
    _start(client, trigger="MRC directed")
    data = get_model("M1")["data"]
    assert len(data["review_signoffs"]) == 1
    assert [d for d in data["documents"] if d["category"] == "Model Review Report"]
    # ...and the new cycle has to be worked through again before signing off.
    blocked = client.post("/api/models/M1/review/sign-off",
                          json={"commentary": "Again", "confirmed": True}, headers=HEADERS)
    assert blocked.status_code == 400


def test_an_invented_trigger_is_refused(client):
    _register(client)
    assert _start(client, trigger="Because I felt like it").status_code == 400


def test_starting_a_cycle_on_an_unknown_model_is_404(client):
    assert client.post("/api/models/NOPE/review/start-cycle",
                       json={"trigger": "Periodic", "confirmed": True},
                       headers=HEADERS).status_code == 404
