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
"""Signing off a review: the gate, the attestation and the report it files.

The sign-off is the moment a review stops being work in progress and becomes a
document somebody's committee will rely on. So it refuses to happen while any
stage is unagreed or any challenge is unanswered, it records who said it, and it
files the report there and then — because a report generated later would describe
a record that had moved on.
"""
from __future__ import annotations

import pytest

from config.governance import REVIEW_STAGES
from tests.web.conftest import HEADERS


@pytest.fixture(autouse=True)
def _stub_pdf(monkeypatch):
    """The report's content is tested against its LaTeX; here only the filing matters.

    Patched where the report module bound it, not where it is defined: the import
    is by name, so stubbing the source module would leave the real compiler in
    place — as it did, quietly producing a 48KB PDF on every run.
    """
    monkeypatch.setattr("src.governance.model_inventory.review_report.compile_tex",
                        lambda tex, assets=None: b"%PDF-review")


def _register(client):
    return client.post(
        "/api/models",
        json={"model_id": "M1", "name": "Alpha", "confirmed": True,
              "fields": {"owner": "owner@corp", "peer_reviewer": "rev@corp"}},
        headers=HEADERS,
    )


def _agree_all(client, skip=None):
    for stage in REVIEW_STAGES:
        if stage["key"] == skip:
            continue
        client.post("/api/models/M1/review/approve-stage",
                    json={"stage": stage["key"], "confirmed": True}, headers=HEADERS)


def _sign(client, commentary="Fit for use with the limitations recorded."):
    return client.post("/api/models/M1/review/sign-off",
                       json={"commentary": commentary, "confirmed": True}, headers=HEADERS)


def _blockers(client):
    return client.get("/api/models/M1/review/blockers").get_json()["blockers"]


def test_a_review_with_stages_outstanding_cannot_be_signed_off(client):
    _register(client)
    _agree_all(client, skip="monitoring")
    assert _blockers(client) == ["Monitoring approach not agreed"]
    response = _sign(client)
    assert response.status_code == 400
    assert "Monitoring approach not agreed" in response.get_json()["error"]


def test_an_open_challenge_blocks_the_sign_off(client):
    """A reviewer who means to sign off over a challenge has to answer it in
    writing first, rather than signing past it in silence."""
    _register(client)
    _agree_all(client)
    client.post("/api/models/M1/review/note",
                json={"stage": "questions", "text": "Benchmark is not comparable",
                      "kind": "Challenge"}, headers=HEADERS)
    assert any("open challenge" in b for b in _blockers(client))
    assert _sign(client).status_code == 400

    raised = client.get("/api/models/M1").get_json()["data"]["review_notes"][0]
    client.post("/api/models/M1/review/note",
                json={"stage": "questions", "text": "Swapped for a like-for-like book",
                      "resolves": raised["item_id"]}, headers=HEADERS)
    assert _blockers(client) == []
    assert _sign(client).status_code == 201


def test_signing_off_records_the_attestation_and_files_the_report(client):
    _register(client)
    _agree_all(client)
    data = _sign(client).get_json()["data"]

    signed = data["review_signoffs"][0]
    assert signed["commentary"] == "Fit for use with the limitations recorded."
    assert signed["signed_by"] == HEADERS["X-Auth-Request-User"]
    assert signed["signed_at"] and signed["report_filename"]
    assert data["review_status"] == "Signed off"

    # Filed apart from the reviewer's working papers: what the committee is given
    # is the signed report, and only that is a document anybody should be tabling.
    filed = [d for d in data["documents"] if d["category"] == "Model Review Report"]
    assert len(filed) == 1
    assert filed[0]["filename"] == signed["report_filename"]
    served = client.get(f"/api/models/M1/documents/{filed[0]['item_id']}/download")
    assert served.status_code == 200 and served.data == b"%PDF-review"


def test_a_sign_off_needs_the_reviewers_commentary(client):
    _register(client)
    _agree_all(client)
    assert _sign(client, commentary="   ").status_code == 400
    assert client.get("/api/models/M1").get_json()["data"].get("review_signoffs") in (None, [])


def test_a_sign_off_cannot_be_rewritten_afterwards(client):
    """An attestation that could be edited later would not be an attestation."""
    _register(client)
    _agree_all(client)
    _sign(client)
    item_id = client.get("/api/models/M1").get_json()["data"]["review_signoffs"][0]["item_id"]
    response = client.post(
        f"/api/models/M1/collections/review_signoffs/{item_id}",
        json={"fields": {"commentary": "Actually, no"}, "confirmed": True}, headers=HEADERS,
    )
    assert response.status_code == 400
    assert "append-only" in response.get_json()["error"]


def test_blockers_on_an_unknown_model_is_404(client):
    assert client.get("/api/models/NOPE/review/blockers").status_code == 404


def test_signing_off_a_model_nobody_registered_is_404(client):
    response = client.post("/api/models/NOPE/review/sign-off",
                           json={"commentary": "Reviewed.", "confirmed": True},
                           headers=HEADERS)
    assert response.status_code == 404
