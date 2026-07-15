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
"""Pure tests for ingest schema + cross-reference validation."""
from __future__ import annotations

import json

import pytest

from config.paths import CONTRACTS_V1_DIR
from src.ingest._validate import (
    SchemaValidationError,
    validate_envelope,
    validate_payload,
)


def _example(name: str) -> dict:
    return json.loads((CONTRACTS_V1_DIR / "examples" / name).read_text())


def test_valid_envelope_passes():
    validate_envelope(_example("envelope.example.json"))


def test_envelope_missing_provenance_raises():
    body = _example("envelope.example.json")
    del body["provenance"]
    with pytest.raises(SchemaValidationError) as exc:
        validate_envelope(body)
    assert exc.value.errors  # carries human-readable detail


def test_valid_data_lineage_payload_passes():
    validate_payload("data-lineage", _example("data_lineage.example.json"))


def test_valid_model_inventory_payload_passes():
    # model-inventory has no cross-ref checker yet: exercises the None branch.
    validate_payload("model-inventory", _example("model_inventory.example.json"))


def test_data_lineage_schema_violation_raises():
    payload = _example("data_lineage.example.json")
    del payload["runs"]
    with pytest.raises(SchemaValidationError, match="data-lineage payload"):
        validate_payload("data-lineage", payload)


def test_unknown_artifact_raises():
    with pytest.raises(SchemaValidationError, match="unknown artifact"):
        validate_payload("nonsense", {})


def test_data_lineage_cross_reference_failure_raises():
    # runs references a step that has no entry in steps.
    payload = {"runs": {"r1": ["ghost"]}, "steps": {"real": {
        "run_id": "r1", "generator": "g", "status": "success",
        "inputs": {}, "outputs": {},
    }}}
    with pytest.raises(SchemaValidationError, match="cross-reference") as exc:
        validate_payload("data-lineage", payload)
    assert any("ghost" in e for e in exc.value.errors)
