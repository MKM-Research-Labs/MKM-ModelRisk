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
"""Freeze test for the v1 ingest contract: schemas are valid and accept the
example payloads; the envelope enforces its structure and its payload validates
against the artifact schema. This is the Phase 0 Workstream A guardrail — the
schemas under ``contracts/ingest/v1`` are the contract every producer codes to.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

CONTRACTS = Path(__file__).resolve().parents[2] / "contracts" / "ingest" / "v1"
EXAMPLES = CONTRACTS / "examples"

# schema file -> example file. Every artifact schema has a matching example that
# was sliced from real PhysicalRisk data (document is representative).
PAIRS = {
    "envelope.schema.json": "envelope.example.json",
    "model_inventory.schema.json": "model_inventory.example.json",
    "model_chain.schema.json": "model_chain.example.json",
    "data_lineage.schema.json": "data_lineage.example.json",
    "field_lineage.schema.json": "field_lineage.example.json",
    "document.schema.json": "document.example.json",
}


def _load(path: Path) -> dict:
    return json.loads(path.read_text())


def _schema(name: str) -> dict:
    return _load(CONTRACTS / name)


def _example(name: str) -> dict:
    return _load(EXAMPLES / name)


@pytest.mark.parametrize("schema_name", sorted(PAIRS))
def test_schema_is_valid_jsonschema(schema_name: str) -> None:
    # The schema itself must be a well-formed Draft 2020-12 schema.
    Draft202012Validator.check_schema(_schema(schema_name))


@pytest.mark.parametrize("schema_name,example_name", sorted(PAIRS.items()))
def test_example_matches_schema(schema_name: str, example_name: str) -> None:
    Draft202012Validator(_schema(schema_name)).validate(_example(example_name))


def test_every_schema_has_an_example() -> None:
    # Guard against adding a schema without a paired, validated example.
    schemas = {p.name for p in CONTRACTS.glob("*.schema.json")}
    assert schemas == set(PAIRS), schemas ^ set(PAIRS)


def test_envelope_payload_matches_artifact_schema() -> None:
    # The example envelope declares artifact=data-lineage; its payload must
    # validate against the data-lineage schema.
    env = _example("envelope.example.json")
    assert env["artifact"] == "data-lineage"
    Draft202012Validator(_schema("data_lineage.schema.json")).validate(env["payload"])


def test_envelope_requires_provenance() -> None:
    env = _example("envelope.example.json")
    del env["provenance"]
    with pytest.raises(ValidationError):
        Draft202012Validator(_schema("envelope.schema.json")).validate(env)


def test_envelope_rejects_unknown_top_level_key() -> None:
    env = _example("envelope.example.json")
    env["surprise"] = True  # additionalProperties: false on the envelope
    with pytest.raises(ValidationError):
        Draft202012Validator(_schema("envelope.schema.json")).validate(env)


def test_provenance_requires_all_fields() -> None:
    env = _example("envelope.example.json")
    del env["provenance"]["commit"]
    with pytest.raises(ValidationError):
        Draft202012Validator(_schema("envelope.schema.json")).validate(env)


def test_data_lineage_requires_runs_and_steps() -> None:
    payload = _example("data_lineage.example.json")
    del payload["runs"]
    with pytest.raises(ValidationError):
        Draft202012Validator(_schema("data_lineage.schema.json")).validate(payload)


def test_model_requires_id_and_name() -> None:
    payload = _example("model_inventory.example.json")
    del payload["models"][0]["model_id"]
    with pytest.raises(ValidationError):
        Draft202012Validator(_schema("model_inventory.schema.json")).validate(payload)


def test_field_lineage_field_requires_source() -> None:
    payload = _example("field_lineage.example.json")
    report = next(iter(payload["reports"].values()))
    section = next(iter(report["sections"].values()))
    field = next(iter(section["fields"].values()))
    del field["source_file"]
    with pytest.raises(ValidationError):
        Draft202012Validator(_schema("field_lineage.schema.json")).validate(payload)
