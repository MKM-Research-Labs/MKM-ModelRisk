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
"""The PhysicalRisk -> ModelRisk demo seed (``app.py phys``).

Maps a source model's scalar fields and collections onto a freshly registered
ModelRisk model, carries the SR 26-2 validation-question statuses across, and
attaches a guide PDF where one is on disk. Idempotent at the model level.
"""
from __future__ import annotations

from scripts import migrate_phys
from src.governance.model_inventory import (
    derive_chain, get_model, register_model, rebuild_inventory_view,
)

MODEL = {
    "model_id": "MKM-XX-001", "name": "Test Model", "short_name": "XX",
    "tier": 2, "materiality": "High", "complexity": "Low", "rag_rating": "Amber",
    "lifecycle_stage": "Production", "validation_status": "Validated", "owner": "Alice",
    "next_review_date": "2026-09-01", "rag_rating_note": "ignored — no such field",
    "assumptions": [{"id": "A1", "description": "assume x", "impact": "High",
                     "monitoring": "watch", "mitigation": "cap"}],
    "limitations": [{"id": "L1", "description": "limit y", "impact": "Medium",
                     "monitoring_trigger": "drift", "compensating_control": "overlay"}],
    "known_failure_modes": ["fails on tiny probs", "", "numeric blow-up"],
    "remediation_steps": [{"id": "R1", "description": "fix z", "owner": "Bob",
                           "priority": "High", "due_date": "2026-03-01", "status": "Open"}],
    "version_history": [{"version": "0.1.0", "date": "2025-10-01", "author": "Alice",
                         "description": "init", "document": "g.pdf"}],
    "validation_questions": [{"question_id": "1", "status": "Addressed", "evidence": "quantlib"},
                             {"question_id": "bad", "status": "Addressed"}],
}


def test_migrate_model_maps_fields_collections_and_validation_questions():
    assert migrate_phys.migrate_model(MODEL) is True
    rebuild_inventory_view()
    data = get_model("MKM-XX-001")["data"]
    assert data["materiality"] == "High" and data["rag_rating"] == "Amber"
    assert data["lifecycle_stage"] == "Production" and data["owner"] == "Alice"
    assert data["assumptions"][0]["description"] == "assume x"
    assert data["limitations"][0]["compensating_control"] == "overlay"
    # Free-text failure modes become weaknesses; the empty one is dropped.
    assert [w["description"] for w in data["model_weaknesses"]] == ["fails on tiny probs", "numeric blow-up"]
    assert data["remediation_steps"][0]["owner"] == "Bob"
    assert data["version_history"][0]["ref_document"] == "g.pdf"
    vq1 = next(q for q in data["validation_questions"] if q["item_id"] == "VQ-001")
    assert vq1["status"] == "Addressed" and vq1["evidence"] == "quantlib"


def test_migrate_model_skips_an_already_registered_model():
    register_model(model_id="MKM-XX-001", name="Already here", actor="someone")
    rebuild_inventory_view()
    assert migrate_phys.migrate_model(MODEL) is False
    # The pre-existing registration is untouched — no assumptions were added.
    assert not get_model("MKM-XX-001")["data"].get("assumptions")


def test_scalar_fields_drops_unknown_and_invalid_choice_values():
    fields = migrate_phys._scalar_fields(
        {"rag_rating": "Purple", "materiality": "High", "no_such_field": "x", "owner": ""})
    assert fields == {"materiality": "High"}  # invalid choice, unknown field, and blank dropped


def _inventory_with_docs(tmp_path, monkeypatch):
    """Two models with their own folder, one whose source path is stale, and two
    that wrongly point at the *same* folder (the MKM-IP-001 / MKM-PV-001 case)."""
    monkeypatch.setattr(migrate_phys, "PHYS_ROOT", tmp_path)
    for folder, names in (("alpha", ("alpha.pdf", "analysis.pdf", "test_results.pdf")),
                          ("shared", ("shared.pdf",))):
        (tmp_path / folder).mkdir()
        for name in names:
            (tmp_path / folder / name).write_bytes(b"%PDF-1.4 demo")
    return {"models": [
        {"model_id": "MKM-AA-001", "documents": [{"path": "alpha/alpha.pdf"}]},
        {"model_id": "MKM-BB-001", "documents": [{"path": "gone/missing.pdf"}]},
        {"model_id": "MKM-CC-001", "documents": [{"path": "shared/shared.pdf"}]},
        {"model_id": "MKM-DD-001", "documents": [{"path": "shared/shared.pdf"}]},
    ]}


def test_attach_documents_walks_the_folder_and_categorises_by_filename(tmp_path, monkeypatch):
    inventory = _inventory_with_docs(tmp_path, monkeypatch)
    for model_id in ("MKM-AA-001", "MKM-BB-001", "MKM-CC-001", "MKM-DD-001"):
        register_model(model_id=model_id, name=model_id, actor="a")
    rebuild_inventory_view()

    result = migrate_phys.attach_documents(inventory)
    rebuild_inventory_view()
    # Only the unambiguous model gets documents — all three PDFs in its folder.
    assert result["attached"] == 3
    docs = {d["filename"]: d["category"] for d in get_model("MKM-AA-001")["data"]["documents"]}
    assert docs == {"alpha.pdf": "Core Documentation", "analysis.pdf": "Analysis",
                    "test_results.pdf": "Test Results"}
    # A stale path leaves the model unresolved; a shared folder makes both ambiguous.
    assert result["unresolved"] == ["MKM-BB-001"]
    assert result["ambiguous"] == ["MKM-CC-001", "MKM-DD-001"]
    for model_id in ("MKM-BB-001", "MKM-CC-001", "MKM-DD-001"):
        assert not get_model(model_id)["data"].get("documents")


def test_attach_documents_is_idempotent(tmp_path, monkeypatch):
    inventory = _inventory_with_docs(tmp_path, monkeypatch)
    register_model(model_id="MKM-AA-001", name="A", actor="a")
    rebuild_inventory_view()
    migrate_phys.attach_documents(inventory)
    rebuild_inventory_view()
    assert migrate_phys.attach_documents(inventory)["attached"] == 0


def test_declare_source_edges_adds_per_model_upstream_and_downstream():
    for model_id in ("MKM-P-001", "MKM-Q-001", "MKM-R-001"):
        register_model(model_id=model_id, name=model_id, actor="a")
    rebuild_inventory_view()
    inventory = {"models": [
        {"model_id": "MKM-Q-001", "upstream_models": ["MKM-P-001"],
         "downstream_models": ["MKM-R-001"]},
        # Unregistered endpoints and self-loops are skipped, not fatal.
        {"model_id": "MKM-R-001", "upstream_models": ["MKM-NOPE-001", "MKM-R-001"]},
    ]}
    assert migrate_phys.declare_source_edges(inventory) == 2
    edges = {(link["from"], link["to"]) for link in derive_chain()["links"]}
    assert edges == {("MKM-P-001", "MKM-Q-001"), ("MKM-Q-001", "MKM-R-001")}
    # Re-running declares nothing new.
    assert migrate_phys.declare_source_edges(inventory) == 0
