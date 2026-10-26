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

"""Recording the Wolfram benchmarks (``scripts.record_wolfram_benchmarks``).

The properties worth protecting: both models end with benchmark_tests = Yes and
VQ-008 Partially Addressed with the benchmark rationale; each re-issued document
(PR-001 v3.1, DE-001 v1.1) is filed as Core Documentation and the document it
supersedes moves to History, keeping its id; a re-run changes nothing; and a missing model or file writes nothing.
"""
from __future__ import annotations

import pytest

from scripts import record_wolfram_benchmarks as record
from src.governance.documents import add_document
from src.governance.model_inventory import get_model, rebuild_inventory_view, register_model
from src.governance.model_inventory.commands import AGGREGATE_TYPE


def _register(with_superseded=True):
    for model_id in record.VQ_RATIONALE:
        register_model(model_id=model_id, name=f"Model {model_id}", actor="test")
    if with_superseded:
        for model_id, spec in record.REISSUES.items():
            add_document(aggregate_type=AGGREGATE_TYPE, aggregate_id=model_id,
                         scope=f"model/{model_id}", category="Core Documentation",
                         filename=spec["superseded"], data=b"%PDF-1.4 old\n%%EOF",
                         description="superseded", actor="test")
    rebuild_inventory_view()


def _docs_dir(tmp_path):
    for model_id, spec in record.REISSUES.items():
        d = tmp_path / model_id
        d.mkdir()
        for name, _ in spec["files"]:
            (d / name).write_bytes(b"%PDF-1.4 new\n%%EOF")
    return tmp_path


def _data(model_id):
    return get_model(model_id)["data"]


def _vq(model_id):
    return next(q for q in _data(model_id)["validation_questions"]
                if q["item_id"] == record.VQ_BENCHMARKING)


def test_both_models_record_the_benchmark(tmp_path):
    _register()
    record.apply(docs_dir=_docs_dir(tmp_path))
    for model_id, rationale in record.VQ_RATIONALE.items():
        assert _data(model_id)["benchmark_tests"] == "Yes"
        assert _vq(model_id)["status"] == "Partially Addressed"
        assert _vq(model_id)["rationale"] == rationale


def test_reissues_are_filed_and_superseded_documents_move_to_history(tmp_path):
    _register()
    old = {m: next(d for d in _data(m)["documents"] if d["original_name"] == spec["superseded"])
           for m, spec in record.REISSUES.items()}
    record.apply(docs_dir=_docs_dir(tmp_path))
    for model_id, spec in record.REISSUES.items():
        docs = {d["original_name"]: d for d in _data(model_id)["documents"]}
        assert docs[spec["superseded"]]["category"] == "History"
        assert docs[spec["superseded"]]["item_id"] == old[model_id]["item_id"]
        for name, _ in spec["files"]:
            assert docs[name]["category"] == "Core Documentation"


def test_it_is_idempotent(tmp_path):
    _register()
    root = _docs_dir(tmp_path)
    record.apply(docs_dir=root)
    assert all(not done for done in record.apply(docs_dir=root).values())


def test_a_missing_file_writes_nothing(tmp_path):
    _register()
    root = _docs_dir(tmp_path)
    (root / "MKM-DE-001" / record.REISSUES["MKM-DE-001"]["files"][1][0]).unlink()
    with pytest.raises(FileNotFoundError, match="delta_engine_v1.1.tex"):
        record.apply(docs_dir=root)
    assert _data("MKM-GH-001").get("benchmark_tests") != "Yes"


def test_an_unregistered_model_writes_nothing(tmp_path):
    register_model(model_id="MKM-GH-001", name="GEV", actor="test")
    rebuild_inventory_view()
    with pytest.raises(RuntimeError, match="MKM-PR-001"):
        record.apply(docs_dir=_docs_dir(tmp_path))
    assert _data("MKM-GH-001").get("benchmark_tests") != "Yes"


def test_the_real_reissued_documents_are_in_the_repo():
    for model_id, spec in record.REISSUES.items():
        for name, _ in spec["files"]:
            assert (record.MODEL_DOCS_DIR / model_id / name).is_file()
