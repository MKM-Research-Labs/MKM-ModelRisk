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

"""Leftover-model sweep (``scripts.sweep_leftover_models``) — WD, WS, BRF.

WD/WS take the standard 4/1/4 assessment; BRF-001's deterministic-transform status
set (with genuine Not Applicable answers) is preserved, not forced to the template.
"""
from __future__ import annotations

from scripts import sweep_leftover_models as sweep
from src.governance.model_inventory import get_model, register_model, rebuild_inventory_view

MODEL_IDS = tuple(sweep.MODELS)


def _register_all():
    for mid in MODEL_IDS:
        register_model(model_id=mid, name=sweep.MODELS[mid]["name"], actor="test")
    rebuild_inventory_view()


def _fake_root(tmp_path):
    for _mid, spec in sweep.MODELS.items():
        d = tmp_path / "docs" / "models" / spec["folder"]
        d.mkdir(parents=True, exist_ok=True)
        (d / "test_results.pdf").write_bytes(b"%PDF-1.5 test\n%%EOF")
    return tmp_path


def _data(mid):
    return get_model(mid)["data"]


def test_it_files_unit_test_and_sets_declarations(tmp_path):
    _register_all()
    sweep.apply(phys_root=_fake_root(tmp_path))
    for mid in MODEL_IDS:
        d = _data(mid)
        assert "Unit Test" in {x["category"] for x in d["documents"]}
        assert d["unit_tests"] == "Yes"
        assert d["integration_tests"] == "Yes"
        assert d["benchmark_tests"] == "No"
        assert d["validation_date"] == sweep.MODELS[mid]["validation_date"]


def test_wd_ws_take_the_standard_shape(tmp_path):
    _register_all()
    sweep.apply(phys_root=_fake_root(tmp_path))
    for mid in ("MKM-WD-001", "MKM-WS-001"):
        by_id = {q["item_id"]: q for q in _data(mid)["validation_questions"]}
        assert by_id["VQ-002"]["status"] == "Partially Addressed"
        assert by_id["VQ-005"]["status"] == "Not Addressed"
        assert by_id["VQ-008"]["status"] == "Not Addressed"


def test_brf_preserves_its_not_applicable_answers(tmp_path):
    _register_all()
    sweep.apply(phys_root=_fake_root(tmp_path))
    by_id = {q["item_id"]: q for q in _data("MKM-BRF-001")["validation_questions"]}
    # deterministic transform: these are genuinely Not Applicable, not Not Addressed
    for na in ("VQ-004", "VQ-005", "VQ-008"):
        assert by_id[na]["status"] == "Not Applicable"
        assert by_id[na]["rationale"]
    assert by_id["VQ-002"]["status"] == "Addressed"        # not downgraded to Partial
    assert by_id["VQ-009"]["status"] == "Not Addressed"    # honest: no independent validation
    assert all(by_id[f"VQ-00{n}"]["rationale"] for n in range(1, 10))


def test_it_is_idempotent(tmp_path):
    root = _fake_root(tmp_path)
    _register_all()
    sweep.apply(phys_root=root)
    again = sweep.apply(phys_root=root)
    assert again == [
        {"model": mid, "fields": [], "questions": 0, "documents": []}
        for mid in MODEL_IDS
    ]
