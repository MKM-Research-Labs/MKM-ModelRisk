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
"""Tests for the per-model client pack (ZIP)."""
from __future__ import annotations

import io
import zipfile

import pytest

from src.governance.model_inventory.client_pack import build_model_pack

MODEL = {"model_id": "M1", "data": {
    "name": "Alpha",
    "documents": [
        {"category": "Core Documentation", "filename": "core.pdf", "original_name": "core.pdf"},
        {"category": "Analysis", "filename": "sensitivity.pdf", "original_name": "sensitivity.pdf"},
        {"category": "Analysis", "filename": "sensitivity.tex", "original_name": "sensitivity.tex"},
        {"category": "Test Results", "filename": "tests.pdf", "original_name": "tests.pdf"},
        "not-a-dict",
    ],
}}

SETTINGS = {"fields": {"org_name": "MKM"}}


@pytest.fixture
def uploads(tmp_path, monkeypatch):
    """A model upload directory holding every attachment but ``tests.pdf``, so the
    missing-file path is exercised alongside the happy one."""
    scope = tmp_path / "model" / "M1"
    scope.mkdir(parents=True)
    for name in ("core.pdf", "sensitivity.pdf", "sensitivity.tex"):
        (scope / name).write_bytes(b"%PDF-" + name.encode())
    monkeypatch.setattr("src.files.store.UPLOAD_DIR", tmp_path)
    monkeypatch.setattr("src.governance.mrc.pack.compile_tex",
                        lambda tex, assets=None: b"%PDF-stub")
    return tmp_path


def _open(pack):
    return zipfile.ZipFile(io.BytesIO(pack))


def test_pack_carries_the_document_and_its_pdf_evidence(uploads):
    archive = _open(build_model_pack(MODEL, SETTINGS, "2026-06-22"))
    names = archive.namelist()
    assert "M1_model_risk_document.pdf" in names
    assert "Core Documentation/core.pdf" in names
    assert "Analysis/sensitivity.pdf" in names


def test_pack_leaves_out_the_latex_sources(uploads):
    """The source filed beside a PDF is the same document in a form no recipient
    wants, and it is the one thing in the pack a client could not open."""
    assert "Analysis/sensitivity.tex" not in _open(
        build_model_pack(MODEL, SETTINGS, "2026-06-22")).namelist()


def test_pack_states_what_it_could_not_include(uploads):
    """A file recorded on the model but absent from disk is named in CONTENTS rather
    than dropped: a silently short pack reads as a complete one."""
    archive = _open(build_model_pack(MODEL, SETTINGS, "2026-06-22"))
    contents = archive.read("CONTENTS.txt").decode()
    assert "Test Results/tests.pdf" not in archive.namelist()
    assert "not available at the time of packing" in contents
    assert "Test Results/tests.pdf" in contents


def test_pack_contents_names_the_model_and_lists_what_is_inside(uploads):
    contents = _open(build_model_pack(MODEL, SETTINGS, "2026-06-22")).read(
        "CONTENTS.txt").decode()
    assert "M1 --- Alpha" in contents
    assert "generated 2026-06-22" in contents
    assert "Core Documentation/core.pdf" in contents


def test_pack_regenerates_the_document_rather_than_filing_a_stored_copy(uploads):
    """The write-up is built at packing time, so a pack cannot carry a stale
    description of the model it is about."""
    archive = _open(build_model_pack(MODEL, SETTINGS, "2026-06-22"))
    assert archive.read("M1_model_risk_document.pdf") == b"%PDF-stub"
