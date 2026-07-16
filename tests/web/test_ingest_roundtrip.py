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
"""Phase 0 exit criterion: the real modelrisk-scan client, end to end.

Drives the actual ``modelrisk_scan.IngestClient`` (envelope construction,
provenance, status/idempotency interpretation) against the live Flask app over an
injected transport that speaks to the app's test client. Skipped where the
``modelrisk-scan`` package is not installed (``pip install -e
packages/modelrisk-scan``).
"""
from __future__ import annotations

import pytest

pytest.importorskip("modelrisk_scan")

from modelrisk_scan import IngestClient, IngestError, build_provenance  # noqa: E402

from config.ingest import INGEST_DEV_TOKEN, INGEST_TOKEN_HEADER  # noqa: E402
from src.web import create_app  # noqa: E402

MANIFEST = {
    "runs": {"run-20260715": ["gaugehd"]},
    "steps": {"gaugehd": {"run_id": "run-20260715", "generator": "port.gauge",
                          "status": "success",
                          "inputs": {"gauge.json": {"hash": None, "type": "file"}},
                          "outputs": {"gaugehd/": {"hash": "abc", "type": "directory"}}}},
}


def _transport_over(test_client):
    """Route the client's HTTP calls through the Flask app's test client."""
    def _post(url, body, headers):
        resp = test_client.post(url, json=body, headers=headers)
        return resp.status_code, resp.get_json()
    return _post


@pytest.fixture
def collector():
    app = create_app(run_db_migrations=False)
    app.testing = True
    return app.test_client()


def test_data_lineage_roundtrip_via_client(collector):
    client = IngestClient("", INGEST_DEV_TOKEN, transport=_transport_over(collector))
    prov = build_provenance(
        source_repo="PhysicalRisk", producer="modelrisk-scan/data-lineage",
        producer_version="0.1.0", commit="d097fae",
    )

    # 1. First push is stored.
    result = client.push("data-lineage", MANIFEST, prov)
    assert result.created is True
    assert result.receipt["data"]["source_repo"] == "PhysicalRisk"
    assert result.receipt["data"]["summary"]["step_count"] == 1

    # 2. Re-pushing identical content is idempotent.
    assert client.push("data-lineage", MANIFEST, prov).created is False

    # 3. Status reflects exactly one accepted receipt for the repo.
    status = collector.get(
        "/api/ingest/status/data-lineage",
        headers={INGEST_TOKEN_HEADER: INGEST_DEV_TOKEN},
    ).get_json()
    assert [r["data"]["source_repo"] for r in status["receipts"]] == ["PhysicalRisk"]

    # 4. A cross-reference-broken manifest is rejected with 422.
    with pytest.raises(IngestError) as exc:
        client.push("data-lineage", {"runs": {"r": ["ghost"]}, "steps": {}}, prov)
    assert exc.value.status == 422
    assert exc.value.body["details"]
