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
"""Tests for the product pack — the ZIP of a product's document plus the full pack
of every model it binds."""
from __future__ import annotations

import io
import zipfile

import pytest

from src.governance.product.pack import build_product_pack, pack_manifest

SETTINGS = {"fields": {"org_name": "MKM"}}


@pytest.fixture
def stub(tmp_path, monkeypatch):
    """Stub the LaTeX compiler, resolve one component model, and point the upload
    dir at a temp tree seeded with a model attachment and a product attachment."""
    monkeypatch.setattr("src.files.store.UPLOAD_DIR", tmp_path)
    monkeypatch.setattr("src.governance.mrc.pack.compile_tex",
                        lambda tex, assets=None: b"%PDF-stub")
    resolver = lambda mid, config=None: {"model_id": mid, "data": {
        "name": "Event Frequency",
        "documents": [
            {"category": "Test Results", "filename": "tests.pdf", "original_name": "tests.pdf"},
            {"category": "Analysis", "filename": "gone.pdf", "original_name": "gone.pdf"},
        ]}} if mid == "MKM-EF-001" else None
    monkeypatch.setattr("src.governance.product.pack.get_model", resolver)
    monkeypatch.setattr("src.governance.product._report_product.get_model", resolver)
    (tmp_path / "model" / "MKM-EF-001").mkdir(parents=True)
    (tmp_path / "model" / "MKM-EF-001" / "tests.pdf").write_bytes(b"%PDF-tests")
    (tmp_path / "product" / "PRD-1").mkdir(parents=True)
    (tmp_path / "product" / "PRD-1" / "cover.pdf").write_bytes(b"%PDF-cover")
    return tmp_path


def _product(components, documents=None):
    return {"product_id": "PRD-1", "data": {
        "product": "Government Bond", "identifier": "X",
        "components": components, "documents": documents or []}}


def _open(data):
    return zipfile.ZipFile(io.BytesIO(data))


def test_pack_bundles_the_product_document_and_each_model_full_pack(stub):
    archive = _open(build_product_pack(
        _product([{"model_id": "MKM-EF-001"}]), SETTINGS, "2026-08-03"))
    names = archive.namelist()
    assert "PRD-1_product_document.pdf" in names            # the product's own document
    assert "models/MKM-EF-001/MKM-EF-001_model_risk_document.pdf" in names
    assert "models/MKM-EF-001/Test Results/tests.pdf" in names   # the model's evidence
    # A recorded-but-absent model attachment is named in CONTENTS, not dropped.
    contents = archive.read("CONTENTS.txt").decode()
    assert "models/MKM-EF-001/Analysis/gone.pdf" in contents
    assert "Identifier: X" in contents


def test_pack_dedupes_components_and_skips_blank_and_malformed_ones(stub):
    archive = _open(build_product_pack(
        _product([{"model_id": "MKM-EF-001"}, {"model_id": "MKM-EF-001"},   # duplicate
                  {"model_id": ""}, {"role": "no id"}, "not-a-dict"]),
        SETTINGS, "2026-08-03"))
    docs = [n for n in archive.namelist()
            if n.endswith("MKM-EF-001_model_risk_document.pdf")]
    assert len(docs) == 1, "the same bound model is packed once"


def test_pack_notes_a_component_model_absent_from_the_inventory(stub):
    contents = _open(build_product_pack(
        _product([{"model_id": "MKM-GONE-001"}]), SETTINGS, "2026-08-03")
    ).read("CONTENTS.txt").decode()
    assert "models/MKM-GONE-001 (not in the inventory)" in contents


def test_pack_carries_product_attachments_and_notes_missing_ones(stub):
    archive = _open(build_product_pack(
        _product([{"model_id": "MKM-EF-001"}], documents=[
            {"category": "Monitoring", "filename": "cover.pdf", "original_name": "cover.pdf"},
            {"category": "Monitoring", "filename": "gone.pdf", "original_name": "gone.pdf"}]),
        SETTINGS, "2026-08-03"))
    assert "product_documents/Monitoring/cover.pdf" in archive.namelist()
    contents = archive.read("CONTENTS.txt").decode()
    assert "product_documents/Monitoring/gone.pdf (recorded but file missing)" in contents


def test_pack_with_nothing_missing_lists_no_missing_section(stub):
    # A product with no components and no attachments: nothing can be missing, so
    # the CONTENTS carries only the "contains" section.
    contents = _open(build_product_pack(
        _product([]), SETTINGS, "2026-08-03")).read("CONTENTS.txt").decode()
    assert "not available at the time of packing" not in contents
    assert "PRD-1_product_document.pdf" in contents


def test_manifest_previews_models_and_attachments_without_compiling(stub):
    m = pack_manifest(_product([{"model_id": "MKM-EF-001"}], documents=[
        {"item_id": "DOC-1", "category": "Monitoring", "filename": "cover.pdf",
         "original_name": "cover.pdf"}]), SETTINGS)
    assert m["models"][0] == {"model_id": "MKM-EF-001", "name": "Event Frequency",
                              "present": True, "attachments": ["gone.pdf", "tests.pdf"]}
    assert m["attachments"][0] == {"name": "cover.pdf", "item_id": "DOC-1", "present": True}
    assert m["includes_product_document"] is True
    # The model's gone.pdf is recorded but absent -> a warning up front.
    assert any("gone.pdf" in w for w in m["warnings"])


def test_manifest_warns_on_unknown_model_missing_attachment_and_no_components(stub):
    m = pack_manifest(_product([{"model_id": "MKM-GONE-001"}], documents=[
        {"filename": "gone.pdf", "original_name": "gone.pdf"}]), SETTINGS)
    assert m["models"][0]["present"] is False
    assert m["attachments"][0]["present"] is False
    joined = " ".join(m["warnings"])
    assert "not in the inventory" in joined and "gone.pdf" in joined

    empty = pack_manifest(_product([]), SETTINGS)
    assert any("binds no component models" in w for w in empty["warnings"])
