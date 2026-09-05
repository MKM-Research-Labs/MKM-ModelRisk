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
"""Tests for the risk-policy HTTP API: the registry, per-division detail, and propose."""
from __future__ import annotations

import io

from src.files import upload_path
from tests.web.conftest import HEADERS


def test_registry_returns_seed_and_per_division_policies(client):
    reg = client.get("/api/risk-policy").get_json()
    assert set(reg) == {"seed", "divisions", "states"}
    ratings = {r["name"]: (r["colour"], r["score"]) for r in reg["seed"]["risk_ratings"]}
    assert ratings["Red"] == ("#d32f2f", 1.25)
    assert ratings["Green"] == ("#388e3c", 1.0)
    # A division with no ratified policy resolves to the seed.
    assert isinstance(reg["divisions"], dict)
    for policy in reg["divisions"].values():
        assert policy["risk_ratings"] == reg["seed"]["risk_ratings"]


def test_registry_reports_the_lifecycle_state_of_each_division(client):
    """A model's Risk tab offers the APPROVED bands, so it has to be able to say when a
    newer draft is sitting with the MRC — otherwise an admin edit that has not been
    ratified simply looks like it never arrived."""
    div = "StateDiv"
    client.post("/api/reference/collections/division",
                json={"fields": {"value": div}, "confirmed": True}, headers=HEADERS)
    assert client.get("/api/risk-policy").get_json()["states"][div]["state"] == "seed"
    _propose_edit(client, div)
    assert client.get("/api/risk-policy").get_json()["states"][div]["state"] == "draft"
    client.post(f"/api/risk-policy/{div}/approve",
                json={"meeting_id": "MTG-STATE", "confirmed": True}, headers=HEADERS)
    state = client.get("/api/risk-policy").get_json()["states"][div]
    assert state["state"] == "approved"
    assert state["approved_at"]  # when the live categorisation was ratified


def test_division_detail_defaults_to_the_seed(client):
    detail = client.get("/api/risk-policy/UntouchedDivision").get_json()
    assert detail["state"] == "seed"
    assert detail["draft"] is None
    assert detail["live"]["risk_ratings"] == detail["seed"]["risk_ratings"]


def test_propose_saves_a_draft_without_going_live(client):
    div = "TestProposeDiv"
    policy = client.get(f"/api/risk-policy/{div}").get_json()["seed"]
    policy["risk_ratings"][0]["colour"] = "#000000"
    resp = client.post(f"/api/risk-policy/{div}/propose",
                       json={"policy": policy, "confirmed": True}, headers=HEADERS)
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["state"] == "draft"
    assert body["draft"]["risk_ratings"][0]["colour"] == "#000000"
    # The live policy is unchanged until the division's MRC signs the draft off.
    assert body["live"]["risk_ratings"][0]["colour"] != "#000000"


def test_propose_rejects_a_broken_policy(client):
    policy = client.get("/api/risk-policy/BadDiv").get_json()["seed"]
    policy["grid"] = {}  # no longer covers the Mission-Criticality bands
    resp = client.post("/api/risk-policy/BadDiv/propose",
                       json={"policy": policy, "confirmed": True}, headers=HEADERS)
    assert resp.status_code >= 400


def _propose_edit(client, division, colour="#010203"):
    policy = client.get(f"/api/risk-policy/{division}").get_json()["seed"]
    policy["risk_ratings"][0]["colour"] = colour
    client.post(f"/api/risk-policy/{division}/propose",
                json={"policy": policy, "confirmed": True}, headers=HEADERS)
    return colour


def test_approve_makes_the_draft_live(client):
    div = "ApproveDiv"
    colour = _propose_edit(client, div)
    resp = client.post(f"/api/risk-policy/{div}/approve",
                       json={"meeting_id": "MTG-1", "confirmed": True}, headers=HEADERS)
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["state"] == "approved"
    assert body["draft"] is None
    assert body["live"]["risk_ratings"][0]["colour"] == colour


def test_reject_leaves_the_live_policy_unchanged(client):
    div = "RejectDiv"
    _propose_edit(client, div, "#999999")
    resp = client.post(f"/api/risk-policy/{div}/reject",
                       json={"confirmed": True}, headers=HEADERS)
    body = resp.get_json()
    assert body["state"] == "seed"
    assert body["draft"] is None
    assert body["live"]["risk_ratings"][0]["colour"] != "#999999"


def test_approve_without_a_draft_is_rejected(client):
    resp = client.post("/api/risk-policy/NoDraftDiv/approve",
                       json={"confirmed": True}, headers=HEADERS)
    assert resp.status_code >= 400


def test_categorisation_pdf_renders(client):
    resp = client.get("/api/risk-policy/PdfDiv/categorisation.pdf")
    assert resp.status_code == 200
    assert resp.mimetype == "application/pdf"
    assert resp.data[:4] == b"%PDF"


def test_upload_and_surface_the_policy_document(client, tmp_path, monkeypatch):
    monkeypatch.setattr("src.files.store.UPLOAD_DIR", tmp_path)
    data = {"file": (io.BytesIO(b"%PDF-policy"), "Division Risk Policy.pdf")}
    resp = client.post("/api/risk-policy/DocDiv/document", data=data,
                       content_type="multipart/form-data", headers=HEADERS)
    assert resp.status_code == 201
    assert resp.get_json()["document"]["original_name"] == "Division Risk Policy.pdf"
    # The detail endpoint now surfaces the uploaded document, and it downloads.
    assert client.get("/api/risk-policy/DocDiv").get_json()["document"] is not None
    dl = client.get("/api/risk-policy/DocDiv/document")
    assert dl.status_code == 200 and dl.data == b"%PDF-policy"


def test_uploading_a_policy_document_with_no_file_is_400(client):
    resp = client.post("/api/risk-policy/DocDiv/document", data={},
                       content_type="multipart/form-data", headers=HEADERS)
    assert resp.status_code == 400


def test_an_extension_the_platform_will_not_store_is_400(client, tmp_path, monkeypatch):
    monkeypatch.setattr("src.files.store.UPLOAD_DIR", tmp_path)
    data = {"file": (io.BytesIO(b"x"), "policy.exe")}
    resp = client.post("/api/risk-policy/DocDiv/document", data=data,
                       content_type="multipart/form-data", headers=HEADERS)
    assert resp.status_code == 400


def test_a_division_that_has_filed_no_written_policy_is_404(client):
    assert client.get("/api/risk-policy/NoDocDiv/document").status_code == 404


def test_a_policy_document_whose_file_has_gone_missing_is_404(client, tmp_path,
                                                              monkeypatch):
    """The division still records that it filed one; the file underneath is gone.
    That is a 404 about the file, not a stack trace about the store."""
    monkeypatch.setattr("src.files.store.UPLOAD_DIR", tmp_path)
    client.post("/api/risk-policy/DocDiv/document",
                data={"file": (io.BytesIO(b"%PDF-policy"), "Risk Policy.pdf")},
                content_type="multipart/form-data", headers=HEADERS)
    filename = client.get("/api/risk-policy/DocDiv").get_json()["document"]["filename"]
    upload_path("risk_policy", filename).unlink()
    assert client.get("/api/risk-policy/DocDiv/document").status_code == 404
