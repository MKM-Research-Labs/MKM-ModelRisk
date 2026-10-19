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

"""The Wolfram benchmark attach (scripts.attach_wolfram_benchmark).

Files each model's PhysicalRisk benchmark PDF as a Benchmark Test. The
properties worth protecting: only the PDF is filed, under that category; a
re-run is a no-op; and a missing model or source file stops the run before
anything is written.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from scripts import attach_wolfram_benchmark as attach
from src.governance.model_inventory import get_model, rebuild_inventory_view, register_model


def _register(*ids):
    for model_id in ids or attach.BENCHMARKS:
        register_model(model_id=model_id, name=f"Model {model_id}", actor="test")
    rebuild_inventory_view()


def _fake_output(tmp_path):
    for relpath, _ in attach.BENCHMARKS.values():
        p = tmp_path / relpath
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"%PDF-1.4 benchmark\n%%EOF")
    return tmp_path


def _docs(model_id):
    return {d["original_name"]: d["category"]
            for d in get_model(model_id)["data"].get("documents") or []}


def test_it_files_each_pdf_as_a_benchmark_test(tmp_path):
    _register()
    result = attach.apply(phys_root=_fake_output(tmp_path))
    assert sorted(m for m, _ in result["attached"]) == sorted(attach.BENCHMARKS)
    for model_id, (relpath, _) in attach.BENCHMARKS.items():
        assert _docs(model_id) == {Path(relpath).name: "Benchmark Test"}


def test_one_model_can_be_filed_alone(tmp_path):
    _register()
    attach.apply(["MKM-PR-001"], phys_root=_fake_output(tmp_path))
    assert _docs("MKM-PR-001") and not _docs("MKM-GH-001")


def test_it_is_idempotent(tmp_path):
    _register()
    root = _fake_output(tmp_path)
    attach.apply(phys_root=root)
    assert attach.apply(phys_root=root)["attached"] == []


def test_a_missing_file_writes_nothing(tmp_path):
    _register()
    root = _fake_output(tmp_path)
    (root / attach.BENCHMARKS["MKM-PR-001"][0]).unlink()
    with pytest.raises(FileNotFoundError, match="MKM-PR-001_wolfram_benchmark.pdf"):
        attach.apply(phys_root=root)
    assert _docs("MKM-GH-001") == {}


def test_it_refuses_an_unregistered_or_unknown_model(tmp_path):
    _register("MKM-GH-001")
    with pytest.raises(RuntimeError, match="MKM-PR-001"):
        attach.apply(phys_root=_fake_output(tmp_path))
    with pytest.raises(KeyError, match="MKM-XX-001"):
        attach.apply(["MKM-XX-001"], phys_root=tmp_path)


def test_the_real_spec_points_at_the_generated_benchmarks():
    assert {rel for rel, _ in attach.BENCHMARKS.values()} == {
        "docs/models/gev_hazard_benchmark/MKM-GH-001_wolfram_benchmark.pdf",
        "docs/models/prs_pricing_benchmark/MKM-PR-001_wolfram_benchmark.pdf",
    }
