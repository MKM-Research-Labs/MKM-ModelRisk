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
from src.governance.model_inventory import get_model, register_model, rebuild_inventory_view

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
    registered, docs = migrate_phys.migrate_model(MODEL)
    rebuild_inventory_view()
    assert (registered, docs) == (True, 0)
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
    assert migrate_phys.migrate_model(MODEL) == (False, 0)
    # The pre-existing registration is untouched — no assumptions were added.
    assert not get_model("MKM-XX-001")["data"].get("assumptions")


def test_scalar_fields_drops_unknown_and_invalid_choice_values():
    fields = migrate_phys._scalar_fields(
        {"rag_rating": "Purple", "materiality": "High", "no_such_field": "x", "owner": ""})
    assert fields == {"materiality": "High"}  # invalid choice, unknown field, and blank dropped


def test_attach_documents_reads_a_pdf_on_disk_and_skips_stale_paths(tmp_path, monkeypatch):
    monkeypatch.setattr(migrate_phys, "PHYS_ROOT", tmp_path)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "guide.pdf").write_bytes(b"%PDF-1.4 demo")
    register_model(model_id="MKM-YY-001", name="Docs", actor="a")
    rebuild_inventory_view()
    model = {"documents": [{"path": "docs/guide.pdf", "name": "Guide"},
                           {"path": "docs/missing.pdf"}, "a bare string entry"]}
    assert migrate_phys._attach_documents("MKM-YY-001", model, None) == 1
    rebuild_inventory_view()
    assert get_model("MKM-YY-001")["data"]["documents"][0]["filename"] == "guide.pdf"
