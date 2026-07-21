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
"""End-to-end tests for the generic ingest pipeline (``ingest_payload``)."""
from __future__ import annotations

import pytest

from src.governance.data_lineage import get_manifest, rebuild_data_lineage_view
from src.ingest import SchemaValidationError, ingest_payload

PROV = {
    "source_repo": "PhysicalRisk", "commit": "d097fae", "producer": "modelrisk-scan/data-lineage",
    "producer_version": "0.1.0", "generated_at": "2026-07-15T15:48:22Z",
}
MANIFEST = {
    "runs": {"run-1": ["gaugehd"]},
    "steps": {"gaugehd": {"run_id": "run-1", "generator": "port.gauge", "status": "success",
                          "inputs": {"gauge.json": {"hash": None, "type": "file"}},
                          "outputs": {"gaugehd/": {"hash": "abc", "type": "directory"}}}},
}


def _body(payload=None, provenance=None):
    return {"artifact": "data-lineage", "provenance": provenance or PROV,
            "payload": payload if payload is not None else MANIFEST}


def test_ingest_new_payload_is_created():
    receipt, created = ingest_payload("data-lineage", _body())
    assert created is True
    assert receipt["artifact"] == "data-lineage"
    assert receipt["data"]["source_repo"] == "PhysicalRisk"
    assert receipt["data"]["summary"]["run_count"] == 1
    assert receipt["data"]["summary"]["step_count"] == 1
    # The log now holds both a manifest and a receipt event; rebuilding the
    # manifest view must skip the receipt event and still project the manifest.
    rebuild_data_lineage_view()
    assert get_manifest("PhysicalRisk")["data"]["step_count"] == 1


def test_ingest_identical_payload_is_idempotent():
    ingest_payload("data-lineage", _body())
    receipt, created = ingest_payload("data-lineage", _body())
    assert created is False
    assert receipt["content_hash"] is not None


def test_invalid_envelope_is_rejected():
    bad = _body()
    del bad["provenance"]
    with pytest.raises(SchemaValidationError):
        ingest_payload("data-lineage", bad)


def test_artifact_without_handler_is_rejected():
    # model-inventory has a schema but is not yet wired for ingestion.
    with pytest.raises(SchemaValidationError, match="no ingest handler"):
        ingest_payload("model-inventory", _body())


def test_cross_reference_failure_is_rejected():
    broken = {"runs": {"run-1": ["ghost"]}, "steps": {}}
    with pytest.raises(SchemaValidationError, match="cross-reference"):
        ingest_payload("data-lineage", _body(payload=broken))
