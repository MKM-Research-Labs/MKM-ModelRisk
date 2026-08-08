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
"""The review at the committee: the report is received, the rating is signed off.

The MRC does not adjudicate a review. It signs off the risk rating, and the Model
Review Report is the evidence in front of it when it does — tabled from the model
itself, so the committee reads the document the model actually holds, and named in
the minute so the record shows the rating was granted on a basis rather than
leaving a reader to hope one existed.
"""
from __future__ import annotations

import pytest

from config.governance import REVIEW_STAGES
from tests.web._signoff_flows import (
    _register_subject_model,
    _request_signoff,
    _schedule_meeting,
    _seed_mrc,
    _signoff_item,
    decide,
)
from tests.web.conftest import HEADERS


@pytest.fixture(autouse=True)
def _stub_pdf(monkeypatch):
    monkeypatch.setattr("src.governance.model_inventory.review_report.compile_tex",
                        lambda tex, assets=None: b"%PDF-review")


def _sign_off_a_review(client, model_id="M1"):
    for stage in REVIEW_STAGES:
        client.post(f"/api/models/{model_id}/review/approve-stage",
                    json={"stage": stage["key"], "confirmed": True}, headers=HEADERS)
    return client.post(f"/api/models/{model_id}/review/sign-off",
                       json={"commentary": "Fit for use with the limitations recorded.",
                             "confirmed": True}, headers=HEADERS)


def test_the_signed_report_can_be_tabled_at_the_committee(client):
    """It joins the papers a committee may table against a model in scope — the
    reviewer's working papers do not."""
    _register_subject_model(client)
    _sign_off_a_review(client)
    offered = client.get("/api/models/M1/reviewable-documents").get_json()
    categories = {d["category"] for d in offered}
    assert "Model Review Report" in categories
    assert "Review" not in categories


def test_the_minute_names_the_report_the_committee_received(client):
    _seed_mrc(client)
    _register_subject_model(client)
    _sign_off_a_review(client)
    _schedule_meeting(client)
    _request_signoff(client)
    decide(client, _signoff_item(client)["item_id"])

    minutes = client.get("/api/meetings/MTG1").get_json()["data"]["minutes"]
    text = " ".join(m.get("text") or "" for m in minutes)
    assert "received the Model Review Report" in text
    assert HEADERS["X-Auth-Request-User"] in text


def test_a_rating_signed_off_without_a_review_does_not_claim_one(client):
    """No review, no sentence about one. A minute that implied a report existed
    would be worse than one that stays quiet."""
    _seed_mrc(client)
    _register_subject_model(client)
    _schedule_meeting(client)
    _request_signoff(client)
    decide(client, _signoff_item(client)["item_id"])

    minutes = client.get("/api/meetings/MTG1").get_json()["data"]["minutes"]
    text = " ".join(m.get("text") or "" for m in minutes)
    assert "Model Review Report" not in text
    assert "has granted approval" in text
