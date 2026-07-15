# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
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

from config.ingest import INGEST_DEV_TOKEN, INGEST_TOKEN_HEADER

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
