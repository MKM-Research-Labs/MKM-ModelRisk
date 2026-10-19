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

"""The GH-001 benchmark attach (scripts.attach_gh001_benchmark).

Files the PhysicalRisk Wolfram oracle benchmark under Analysis. The properties
worth protecting: only the PDF is filed, under Analysis; a re-run is a no-op;
and a missing source file stops the run before anything is written.
"""
from __future__ import annotations

import pytest

from scripts import attach_gh001_benchmark as attach
from src.governance.model_inventory import get_model, rebuild_inventory_view, register_model


def _register():
    register_model(model_id=attach.MODEL_ID, name="GEV Hazard Curve Model", actor="test")
    rebuild_inventory_view()


def _fake_output(tmp_path):
    for _, _, rel, _ in attach.DOCS:
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"%PDF-1.4 gev\n%%EOF" if rel.endswith(".pdf") else b"id,value\n")
    return tmp_path


def _docs():
    return {d["original_name"]: d["category"]
            for d in get_model(attach.MODEL_ID)["data"].get("documents") or []}


def test_it_files_only_the_pdf_under_analysis(tmp_path):
    _register()
    result = attach.apply(phys_root=_fake_output(tmp_path))
    assert result["attached"] == [("Analysis", "MKM-GH-001_wolfram_benchmark.pdf")]
    assert _docs() == {"MKM-GH-001_wolfram_benchmark.pdf": "Analysis"}


def test_it_is_idempotent(tmp_path):
    _register()
    root = _fake_output(tmp_path)
    attach.apply(phys_root=root)
    assert attach.apply(phys_root=root)["attached"] == []


def test_a_missing_file_writes_nothing(tmp_path):
    _register()
    root = _fake_output(tmp_path)
    (root / attach.DOCS[-1][2]).unlink()
    with pytest.raises(FileNotFoundError, match="MKM-GH-001_wolfram_benchmark.pdf"):
        attach.apply(phys_root=root)
    assert _docs() == {}


def test_it_refuses_when_the_model_is_absent(tmp_path):
    with pytest.raises(RuntimeError, match="not registered"):
        attach.apply(phys_root=_fake_output(tmp_path))


def test_the_real_spec_points_at_the_generated_benchmark():
    assert [rel for _, _, rel, _ in attach.DOCS] == [
        "docs/models/gev_hazard_benchmark/MKM-GH-001_wolfram_benchmark.pdf"]
