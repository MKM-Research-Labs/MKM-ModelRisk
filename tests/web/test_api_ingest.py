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
"""HTTP tests for the ingest collector endpoints."""
from __future__ import annotations

import pytest

from config.governance import TRAINING_RUNS_COLLECTION
from config.ingest import INGEST_DEV_TOKEN, INGEST_TOKEN_HEADER
from src.governance.ml_application import (get_ml_application,
                                           rebuild_ml_application_view,
                                           register_ml_application)

AUTH = {INGEST_TOKEN_HEADER: INGEST_DEV_TOKEN}

PROV = {
    "source_repo": "PhysicalRisk", "commit": "d097fae", "producer": "modelrisk-scan/data-lineage",
    "producer_version": "0.1.0", "generated_at": "2026-07-15T15:48:22Z",
}
MANIFEST = {
    "runs": {"run-1": ["gaugehd"]},
    "steps": {"gaugehd": {"run_id": "run-1", "generator": "port.gauge", "status": "success",
                          "inputs": {}, "outputs": {}}},
}


def _body(payload=None, provenance=None):
    return {"artifact": "data-lineage", "provenance": provenance or PROV,
            "payload": payload if payload is not None else MANIFEST}


def test_post_data_lineage_created(client):
    resp = client.post("/api/ingest/data-lineage", json=_body(), headers=AUTH)
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["artifact"] == "data-lineage"
    assert body["data"]["summary"]["step_count"] == 1


def test_repost_is_idempotent(client):
    client.post("/api/ingest/data-lineage", json=_body(), headers=AUTH)
    resp = client.post("/api/ingest/data-lineage", json=_body(), headers=AUTH)
    assert resp.status_code == 200


def test_missing_token_is_unauthorised(client):
    resp = client.post("/api/ingest/data-lineage", json=_body())
    assert resp.status_code == 401


def test_wrong_token_is_unauthorised(client):
    resp = client.post("/api/ingest/data-lineage", json=_body(),
                       headers={INGEST_TOKEN_HEADER: "nope"})
    assert resp.status_code == 401


def test_invalid_envelope_is_unprocessable(client):
    bad = _body()
    del bad["provenance"]
    resp = client.post("/api/ingest/data-lineage", json=bad, headers=AUTH)
    assert resp.status_code == 422
    assert resp.get_json()["details"]  # carries schema errors


def test_cross_reference_failure_is_unprocessable(client):
    broken = {"runs": {"run-1": ["ghost"]}, "steps": {}}
    resp = client.post("/api/ingest/data-lineage", json=_body(payload=broken), headers=AUTH)
    assert resp.status_code == 422


def test_status_lists_receipt(client):
    client.post("/api/ingest/data-lineage", json=_body(), headers=AUTH)
    resp = client.get("/api/ingest/status/data-lineage", headers=AUTH)
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["artifact"] == "data-lineage"
    assert len(body["receipts"]) == 1
    assert body["receipts"][0]["data"]["source_repo"] == "PhysicalRisk"


def test_status_empty_for_other_artifact(client):
    client.post("/api/ingest/data-lineage", json=_body(), headers=AUTH)
    resp = client.get("/api/ingest/status/model-inventory", headers=AUTH)
    assert resp.status_code == 200
    assert resp.get_json()["receipts"] == []


def test_status_requires_token(client):
    resp = client.get("/api/ingest/status/data-lineage")
    assert resp.status_code == 401


# --- model-chain endpoint (migration Phase 2) ---

CHAIN = {"description": "string of pearls",
         "links": [{"from": "MKM-SI-001", "to": "MKM-SG-001", "data_handoff": "intensity"},
                   {"from": "MKM-SG-001", "to": "MKM-GH-001", "data_handoff": "gauge series"}]}


def _chain_body(chain=None):
    return {"artifact": "model-chain", "provenance": PROV,
            "payload": chain if chain is not None else CHAIN}


def test_post_model_chain_created(client):
    resp = client.post("/api/ingest/model-chain", json=_chain_body(), headers=AUTH)
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["artifact"] == "model-chain"
    assert body["data"]["summary"]["link_count"] == 2


def test_model_chain_repost_is_idempotent(client):
    client.post("/api/ingest/model-chain", json=_chain_body(), headers=AUTH)
    resp = client.post("/api/ingest/model-chain", json=_chain_body(), headers=AUTH)
    assert resp.status_code == 200


def test_model_chain_cycle_is_unprocessable(client):
    cyclic = {"links": [{"from": "A", "to": "B"}, {"from": "B", "to": "A"}]}
    resp = client.post("/api/ingest/model-chain", json=_chain_body(cyclic), headers=AUTH)
    assert resp.status_code == 422
    assert any("cycle" in d for d in resp.get_json()["details"])


def test_model_chain_status_lists_receipt(client):
    client.post("/api/ingest/model-chain", json=_chain_body(), headers=AUTH)
    resp = client.get("/api/ingest/status/model-chain", headers=AUTH)
    assert resp.status_code == 200
    assert [r["data"]["source_repo"] for r in resp.get_json()["receipts"]] == ["PhysicalRisk"]


REGISTRY = {
    "version": "1.0.0",
    "reports": {"eod_report": {"label": "End of Day", "sections": {
        "summary": {"label": "Summary", "fields": {
            "total_pnl": {"source_file": "blotter.json", "source_field": "pnl"}}}}}},
}


def test_post_field_lineage_created_and_idempotent(client):
    """The field-lineage catalogue (BCBS 239 Principle 3) has its own ingest pipe."""
    body = {"artifact": "field-lineage", "provenance": PROV, "payload": REGISTRY}
    resp = client.post("/api/ingest/field-lineage", json=body, headers=AUTH)
    assert resp.status_code == 201
    summary = resp.get_json()["data"]["summary"]
    assert summary["report_count"] == 1 and summary["field_count"] == 1
    # An identical push is a no-op, reported as 200 rather than 201.
    assert client.post("/api/ingest/field-lineage", json=body,
                       headers=AUTH).status_code == 200


# --- ml-training-run endpoint ---
# The producer here is the code that performed the fit, so what it reports is
# facts about the run. Re-reporting the same fit_id must UPDATE that train: a long
# fit reports as it progresses, and a run that crashes after reporting has to be
# able to report again without becoming two trains.

TRAIN = {"ml_application_id": "MLA-1", "fit_id": "2026-03-03-v1.2",
         "fields": {"snapshot_id": "sha256:ab", "metric_test": "0.9557",
                    "random_seed": "20260303"}}


def _train_body(payload=None):
    return {"artifact": "ml-training-run", "provenance": PROV,
            "payload": payload if payload is not None else TRAIN}


@pytest.fixture
def ml_application():
    register_ml_application(
        ml_application_id="MLA-1", actor="admin",
        fields={"name": "Retail PD scorecard", "division": "Risk", "owner": "Dana",
                "estimator": "GradientBoostingClassifier",
                "use_case": "Ranks retail applicants."})
    rebuild_ml_application_view()


def test_post_ml_training_run_records_the_train(client, ml_application):
    resp = client.post("/api/ingest/ml-training-run", json=_train_body(), headers=AUTH)
    assert resp.status_code == 201
    summary = resp.get_json()["data"]["summary"]
    assert summary["fit_id"] == "2026-03-03-v1.2" and summary["created"] is True
    train = get_ml_application("MLA-1")["data"][TRAINING_RUNS_COLLECTION][0]
    assert train["metric_test"] == "0.9557"


def test_reporting_the_same_fit_again_updates_it_rather_than_adding_one(
        client, ml_application):
    client.post("/api/ingest/ml-training-run", json=_train_body(), headers=AUTH)
    later = {**TRAIN, "fields": {**TRAIN["fields"], "metric_test": "0.9601"}}
    resp = client.post("/api/ingest/ml-training-run", json=_train_body(later),
                       headers=AUTH)
    # 200, not 201: the train already existed. The receipt records the last report.
    assert resp.status_code == 200
    trains = get_ml_application("MLA-1")["data"][TRAINING_RUNS_COLLECTION]
    assert len(trains) == 1 and trains[0]["metric_test"] == "0.9601"


def test_ml_training_run_status_lists_the_receipt(client, ml_application):
    client.post("/api/ingest/ml-training-run", json=_train_body(), headers=AUTH)
    resp = client.get("/api/ingest/status/ml-training-run", headers=AUTH)
    assert [r["data"]["source_repo"] for r in resp.get_json()["receipts"]] \
        == ["PhysicalRisk"]


def test_a_train_without_a_fit_id_is_unprocessable(client, ml_application):
    """The fit_id is what makes a re-report an update; without one the collector
    cannot tell a second report from a second fit."""
    resp = client.post("/api/ingest/ml-training-run",
                       json=_train_body({"ml_application_id": "MLA-1"}), headers=AUTH)
    assert resp.status_code == 422
