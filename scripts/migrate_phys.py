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
"""Populate a ModelRisk instance from the PhysicalRisk model inventory (demo seed).

Registers every source model with as much of its governance data as maps cleanly
(scalar fields, collections and the SR 26-2 validation-question statuses), attaches
the PDFs in each model's documentation folder, builds the model chain from both the
migrated chain artifact and each model's declared upstream/downstream, and creates
the PRS product. Idempotent, so it is safe to re-run; gaps the source cannot resolve
are reported rather than guessed.

Run as:  python -m scripts.migrate_phys   (or  python app.py phys)
"""
from __future__ import annotations

import json
from pathlib import Path

from config.governance import MODEL_FIELD_SPECS, VALID_VQ_STATUSES
from config.paths import PRODUCER_INVENTORY as SOURCE, PRODUCER_ROOT as PHYS_ROOT
from src.governance.documents import add_document
from src.governance.errors import DomainError
from src.governance.model_inventory import (
    add_collection_item,
    derive_chain,
    get_model,
    list_models,
    register_model,
    rebuild_inventory_view,
    update_collection_item,
)
from src.governance.model_inventory.commands import AGGREGATE_TYPE as MODEL_AGGREGATE
from scripts._phys_folders import folder_for
from scripts._phys_lineage import apply_field_renames
from scripts._phys_mapping import COLLECTION_MAP, SCALAR_FIELDS

MODELS_ROOT = PHYS_ROOT / "docs" / "models"
ACTOR = "migrate_phys"



def _valid(field_key: str, value) -> bool:
    """Keep a value only if the field accepts it (choice fields validate their set)."""
    if value in (None, ""):
        return False
    spec = MODEL_FIELD_SPECS.get(field_key)
    if spec and spec.get("type") == "choice":
        return value in spec.get("options", [])
    return True


def _scalar_fields(model: dict) -> dict:
    return {k: model[k] for k in SCALAR_FIELDS if k in model and _valid(k, model.get(k))}


def _map_item(mapping: dict, item: dict) -> dict:
    return {mapping[k]: v for k, v in item.items() if k in mapping and v not in (None, "")}


def _add_collections(model_id: str, model: dict, config) -> None:
    for source_key, (target, mapping) in COLLECTION_MAP.items():
        for item in model.get(source_key) or []:
            if isinstance(item, dict):
                fields = _map_item(mapping, item)
                if fields.get("description"):
                    add_collection_item(model_id=model_id, collection=target, fields=fields,
                                        actor=ACTOR, config=config)
    # Known failure modes are free-text strings in the source -> model weaknesses.
    for weakness in model.get("known_failure_modes") or []:
        if isinstance(weakness, str) and weakness.strip():
            add_collection_item(model_id=model_id, collection="model_weaknesses",
                                fields={"description": weakness}, actor=ACTOR, config=config)


def _update_validation_questions(model_id: str, model: dict, config) -> None:
    """The nine SR 26-2 questions are seeded at registration; carry the source
    status/evidence onto them (matched by question number)."""
    for question in model.get("validation_questions") or []:
        try:
            number = int(question.get("question_id"))
        except (TypeError, ValueError):
            continue
        fields = {}
        if question.get("status") in VALID_VQ_STATUSES:
            fields["status"] = question["status"]
        if question.get("evidence"):
            fields["evidence"] = question["evidence"]
        if fields:
            update_collection_item(model_id=model_id, collection="validation_questions",
                                   item_id=f"VQ-{number:03d}", fields=fields, actor=ACTOR, config=config)


def _classify(filename: str, model_id: str) -> tuple[str, str]:
    """Bucket a document by filename into its ModelRisk category, and give it the
    name it carries in the store — ``(category, stored_filename)``.

    The per-model ``test_results.pdf`` is the model's unit-test evidence, so it
    lands in the Unit Test tab renamed ``unit_tests_<model_id>.pdf`` — one such
    file per model. Everything else keeps its source name and falls to the tab its
    filename implies, defaulting to Core Documentation."""
    low = filename.lower()
    if "test" in low:
        return "Unit Test", f"unit_tests_{model_id}.pdf"
    for hint, category in (("analysis", "Analysis"), ("monitor", "Monitoring")):
        if hint in low:
            return category, filename
    return "Core Documentation", filename


def _doc_dirs(inventory: dict) -> tuple[dict, list, list]:
    """Map each model to its folder -> ``(dirs, ambiguous, unresolved)``. A folder
    belongs to exactly one model, so any two claiming the same one are both skipped
    rather than risk filing another model's documents."""
    claims: dict = {}
    unresolved = []
    for model in inventory.get("models", []):
        folder = folder_for(model, PHYS_ROOT, MODELS_ROOT)
        if folder is None:
            unresolved.append(model.get("model_id"))
        else:
            claims.setdefault(folder, []).append(model.get("model_id"))
    dirs, ambiguous = {}, []
    for folder, model_ids in claims.items():
        if len(model_ids) == 1:
            dirs[model_ids[0]] = folder
        else:
            ambiguous.extend(model_ids)
    return dirs, sorted(ambiguous), sorted(unresolved)


def attach_documents(inventory: dict, config=None) -> dict:
    """Attach every PDF in each model's documentation folder, categorised by name.
    Idempotent — a document already attached is skipped."""
    dirs, ambiguous, unresolved = _doc_dirs(inventory)
    attached = 0
    for model_id, folder in sorted(dirs.items()):
        model = get_model(model_id, config=config)
        if model is None:
            continue
        have = {(d.get("original_name") or d.get("filename"))
                for d in (model["data"].get("documents") or [])}
        for pdf in sorted(folder.glob("*.pdf")):
            category, stored_name = _classify(pdf.name, model_id)
            if stored_name in have:
                continue
            add_document(aggregate_type=MODEL_AGGREGATE, aggregate_id=model_id,
                         scope=f"model/{model_id}", category=category,
                         filename=stored_name, data=pdf.read_bytes(),
                         description="", actor=ACTOR, config=config)
            attached += 1
    return {"attached": attached, "ambiguous": ambiguous, "unresolved": unresolved}


def declare_source_edges(inventory: dict, config=None) -> int:
    """Declare each model's ``upstream_models`` / ``downstream_models``. The migrated
    chain artifact holds only part of the lineage; most of it lives here."""
    registered = {m["model_id"] for m in list_models(config=config)}
    existing = {(link["from"], link["to"]) for link in derive_chain(config=config)["links"]}
    wanted = set()
    for model in inventory.get("models", []):
        model_id = model.get("model_id")
        for producer in model.get("upstream_models") or []:
            wanted.add((producer, model_id))
        for consumer in model.get("downstream_models") or []:
            wanted.add((model_id, consumer))
    declared = 0
    for producer, consumer in sorted(wanted - existing):
        if producer not in registered or consumer not in registered:
            continue
        try:
            add_collection_item(
                model_id=producer, collection="dependencies", actor=ACTOR, config=config,
                fields={"direction": "downstream", "model_id": consumer})
        except DomainError:
            continue  # a self-loop or cycle the guard rejects — leave the chain intact
        rebuild_inventory_view(config=config)
        declared += 1
    return declared


def migrate_model(model: dict, config=None) -> bool:
    """Register one source model with its data. An already-registered model is left
    untouched (idempotent). Documents are attached separately, across the inventory."""
    model_id = model.get("model_id")
    if not model_id or get_model(model_id, config=config) is not None:
        return False
    register_model(model_id=model_id, name=model.get("name") or model_id,
                   fields=_scalar_fields(model), actor=ACTOR, config=config)
    _add_collections(model_id, model, config)
    _update_validation_questions(model_id, model, config)
    return True


def create_prs_product(config=None) -> bool:
    """Create the single PRS product, bound to the PRS pricing model, with a RACI role
    and a sample operational event so the RACI feed-up is demonstrable."""
    from src.governance.product import (
        add_collection_item as product_add, get_product, register_product, rebuild_product_view)
    if get_product("PRD-PRS", config=config) is not None:
        return False
    register_product(product_id="PRD-PRS", product="Physical Risk Swap (PRS)",
                     fields={"analytics_model": "MKM-PR-001",
                             "market_data_model": "Hazard curves (MKM-GH-001)",
                             "calculating_agent": "QuantLib", "tier": 1,
                             "owner": "David K Kelly"}, actor=ACTOR, config=config)
    rebuild_product_view(config=config)
    product_add(product_id="PRD-PRS", collection="raci_roles", actor=ACTOR, config=config,
                fields={"role": "Operations Lead", "raci": "Responsible",
                        "description": "Reruns failed production pricing jobs"})
    product_add(product_id="PRD-PRS", collection="raci_roles", actor=ACTOR, config=config,
                fields={"role": "Model Owner", "raci": "Accountable",
                        "assigned_to": "David K Kelly", "description": "Owns the PRS pricing model"})
    product_add(product_id="PRD-PRS", collection="operational_failure_events", actor=ACTOR, config=config,
                fields={"date": "2026-06-01", "description": "Hazard-curve feed outage delayed the "
                        "overnight PRS spread run", "responsible": "David K Kelly"})
    rebuild_product_view(config=config)
    return True


def migrate(config=None) -> dict:
    """Run the whole demo migration. Returns a count summary."""
    from scripts.backfill_chain import backfill
    from scripts.migrate_model_chain import load_model_chain

    inventory = json.loads(SOURCE.read_text(encoding="utf-8"))
    registered = 0
    for model in inventory.get("models", []):
        if migrate_model(model, config=config):
            registered += 1
    rebuild_inventory_view(config=config)
    # Ingest the source chain, then backfill dependencies + handoffs onto the models.
    load_model_chain(SOURCE, source_repo="PhysicalRisk", config=config)
    chain = backfill(source_repo="PhysicalRisk", config=config)
    # The chain artifact is only part of the lineage; the rest is declared per model.
    edges = declare_source_edges(inventory, config=config)
    docs = attach_documents(inventory, config=config)
    product = create_prs_product(config=config)
    return {"models_registered": registered, "documents_attached": docs["attached"],
            "field_renames": apply_field_renames(ACTOR, config=config),
            "documents_ambiguous": docs["ambiguous"], "documents_unresolved": docs["unresolved"],
            "dependencies": chain["dependencies"], "declared_edges": edges,
            "handoffs": chain["handoffs"], "prs_product": product}


def main() -> int:
    from src.database import run_migrations
    run_migrations()
    result = migrate()
    print(f"models registered: {result['models_registered']}, "
          f"documents attached: {result['documents_attached']}, "
          f"chain: {result['dependencies']} backfilled + {result['declared_edges']} declared, "
          f"handoffs: {result['handoffs']} ({result['field_renames']} field renames), "
          f"PRS product created: {result['prs_product']}")
    # Gaps the source cannot resolve, so the owner knows what to fill in by hand.
    for why, ids in (("two models share one source folder", result["documents_ambiguous"]),
                     ("no source folder on disk", result["documents_unresolved"])):
        if ids:
            print(f"  no documents ({why}): " + ", ".join(ids))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
