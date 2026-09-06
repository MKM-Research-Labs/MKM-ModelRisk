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
"""Ingest validation: JSON Schema plus cross-reference integrity.

Two layers: (1) structural validation of the envelope and the artifact payload
against the frozen ``contracts/ingest/v1`` schemas; (2) cross-reference checks
that span records and cannot be expressed in a schema (e.g. every step named in a
data-lineage ``runs`` list has a matching ``steps`` entry). Both raise
``SchemaValidationError`` carrying a list of human-readable errors.
"""
from __future__ import annotations

import json
from functools import lru_cache
from typing import Any, Callable

from jsonschema import Draft202012Validator

from config.ingest import INGEST_ARTIFACTS
from config.paths import CONTRACTS_V1_DIR
from config.governance._lineage import NODE_KINDS
from src.governance.graph import find_cycle, self_loops

_ENVELOPE_SCHEMA = "envelope.schema.json"


class SchemaValidationError(ValueError):
    """Raised when a payload fails structural or cross-reference validation."""

    def __init__(self, message: str, errors: list[str] | None = None) -> None:
        super().__init__(message)
        self.errors = errors or []


@lru_cache(maxsize=None)
def _validator(schema_file: str) -> Draft202012Validator:
    schema = json.loads((CONTRACTS_V1_DIR / schema_file).read_text())
    return Draft202012Validator(schema)


def _errors(schema_file: str, instance: Any) -> list[str]:
    validator = _validator(schema_file)
    out = []
    for err in sorted(validator.iter_errors(instance), key=lambda e: list(e.path)):
        location = "/".join(str(p) for p in err.path) or "<root>"
        out.append(f"{location}: {err.message}")
    return out


def validate_envelope(body: Any) -> None:
    """Validate the request envelope (provenance + payload)."""
    errors = _errors(_ENVELOPE_SCHEMA, body)
    if errors:
        raise SchemaValidationError("invalid ingest envelope", errors)


def validate_payload(artifact: str, payload: Any) -> None:
    """Validate an artifact payload structurally, then cross-reference it."""
    schema_file = INGEST_ARTIFACTS.get(artifact)
    if schema_file is None:
        raise SchemaValidationError(
            f"unknown artifact: {artifact}",
            [f"'{artifact}' is not an accepted ingest artifact"],
        )
    errors = _errors(schema_file, payload)
    if errors:
        raise SchemaValidationError(f"invalid {artifact} payload", errors)
    _check_cross_refs(artifact, payload)


def _check_data_lineage(payload: dict[str, Any]) -> list[str]:
    """Every step named in a run must have a matching entry in ``steps``."""
    steps = payload.get("steps", {})
    errors = []
    for run_id, step_names in payload.get("runs", {}).items():
        for name in step_names:
            if name not in steps:
                errors.append(f"runs/{run_id}: step '{name}' has no entry in steps")
    return errors


def _check_model_chain(payload: dict[str, Any]) -> list[str]:
    """Graph integrity for the model chain — the generalised ``scan_model_chain``.

    Each link is a directed edge ``from -> to``. A model must not depend on
    itself, and the dependency graph must be acyclic (a cycle would mean the
    'string of pearls' loops back on itself, which cannot be a real pipeline).
    """
    edges = [(l.get("from"), l.get("to")) for l in payload.get("links", [])]
    errors = [f"link {a} -> {b}: a node cannot depend on itself"
              for a, b in self_loops(edges)]
    # A declared kind nobody recognises is refused rather than defaulted. An undeclared
    # kind IS defaulted — every chain pushed before nodes existed is a graph of models —
    # but a typo silently becoming a model is how a foundation model disappears into the
    # estate as something the firm believes it governs.
    for node in payload.get("nodes", []) or []:
        declared = str(node.get("kind") or "").strip()
        if declared and declared.upper() not in NODE_KINDS:
            errors.append(
                f"node {node.get('id')}: unknown kind {declared!r} — "
                f"one of: {', '.join(NODE_KINDS)}")
    known = {str(n.get("id")) for n in (payload.get("nodes") or []) if n.get("id")}
    if known:
        for a, b in edges:
            for end in (a, b):
                if end is not None and str(end) not in known:
                    errors.append(f"link endpoint {end} is not among the declared nodes")
    # Name the cycle. "The chain has a cycle" sends somebody to read the whole graph
    # by hand; the path is what they would have been looking for.
    cycle = find_cycle(edges)
    if cycle:
        errors.append("the model chain has a cycle — the dependency graph must be "
                      "acyclic: " + " -> ".join(str(n) for n in cycle))
    return errors


def _chain_edges(payload: dict[str, Any]) -> list[tuple[str, str]]:
    """The chain's directed edges, from wherever this artifact carries them.

    A standalone ``model-chain`` payload has ``links`` at the top level; a
    ``model-inventory`` carries the same structure nested under ``model_chain``.
    """
    links = payload.get("links")
    if links is None:
        links = payload.get("model_chain", {}).get("links", [])
    return [(link.get("from"), link.get("to")) for link in links]


def _check_model_inventory(payload: dict[str, Any]) -> list[str]:
    """Agreement between the chain's edges and each model's own dependency lists.

    An inventory states its pipeline twice: once as ``model_chain.links``, a list of
    directed edges, and once per model as ``upstream_models`` / ``downstream_models``.
    Neither is derived from the other — both are maintained by hand — so they drift,
    and nothing in a JSON Schema can see it: each half is individually well-formed.

    The drift is not cosmetic. The two halves answer different questions in the
    interface — the chain diagram is drawn from the edges, while "what breaks if this
    model changes" is answered from the per-model lists — so an inventory that
    disagrees with itself gives two different answers to the same governance question
    depending on which screen you are looking at.

    Checked in three parts:

    * every edge endpoint names a model the inventory actually declares, because an
      edge to an unknown model draws a node the inventory cannot describe;
    * every edge appears in both models' lists, and every list entry has an edge;
    * the graph is sound — no self-dependency, no cycle — the same rules the
      standalone chain artifact is already held to, which an inventory's embedded
      chain was not.

    This is the generalised form of PhysicalRisk's full-audit §4.7 scan, which reports
    36 such inconsistencies in the inventory this platform is designed to ingest.
    Reporting them after the fact is weaker than refusing them at the boundary: once
    ingested they are an event in the log, and the log does not rewrite.
    """
    # The schema requires ``models`` to be an array of objects with a model_id, and
    # structural validation has already run by the time this is called, so there is no
    # shape to defend against here.
    models = payload.get("models", [])
    declared = {m.get("model_id") for m in models if m.get("model_id")}
    edges = _chain_edges(payload)
    errors: list[str] = []

    for source, target in edges:
        for endpoint in (source, target):
            if endpoint and endpoint not in declared:
                errors.append(
                    f"model_chain link {source} -> {target}: "
                    f"'{endpoint}' is not a model in this inventory")

    # The edges as the per-model lists would express them, and vice versa.
    from_edges_down: dict[str, set[str]] = {}
    from_edges_up: dict[str, set[str]] = {}
    for source, target in edges:
        from_edges_down.setdefault(source, set()).add(target)
        from_edges_up.setdefault(target, set()).add(source)

    for model in models:
        model_id = model.get("model_id")
        if not model_id:
            continue
        for field, by_edge in (("downstream_models", from_edges_down),
                               ("upstream_models", from_edges_up)):
            stated = set(model.get(field) or ())
            implied = by_edge.get(model_id, set())
            for missing in sorted(implied - stated):
                errors.append(
                    f"{model_id}: the chain has an edge implying "
                    f"{field} contains '{missing}', but it does not")
            # A list entry naming a model this payload does not declare is a forward
            # reference to one ingested separately — inventories arrive in parts, and
            # the bundled example is itself a three-model slice whose last model points
            # onward. Only a reference to a model that IS here can be checked against
            # the chain, and only then is its absence from the links a disagreement.
            for extra in sorted((stated & declared) - implied):
                errors.append(
                    f"{model_id}: {field} lists '{extra}', which is in this inventory "
                    f"but has no matching link in the chain")

    errors.extend(f"link {a} -> {b}: a model cannot depend on itself"
                  for a, b in self_loops(edges))
    # Name the cycle, as the standalone model-chain checker above does. This was
    # written against ``has_cycle`` before that existed; a bare "there is a cycle"
    # sends somebody to read the whole graph by hand, and the path is the thing they
    # were looking for.
    cycle = find_cycle(edges)
    if cycle:
        errors.append("the model chain has a cycle — the dependency graph must be "
                      "acyclic: " + " -> ".join(str(n) for n in cycle))
    return errors


# artifact -> cross-reference checker. field-lineage (pipeline_step resolves to a
# known step) is added with that artifact's ingestion.
_CROSS_REFS: dict[str, Callable[[dict[str, Any]], list[str]]] = {
    "data-lineage": _check_data_lineage,
    "model-chain": _check_model_chain,
    "model-inventory": _check_model_inventory,
}


def _check_cross_refs(artifact: str, payload: Any) -> None:
    checker = _CROSS_REFS.get(artifact)
    if checker is None:
        return
    errors = checker(payload)
    if errors:
        raise SchemaValidationError(
            f"{artifact} cross-reference check failed", errors
        )
