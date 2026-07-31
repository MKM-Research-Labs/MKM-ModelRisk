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

"""Phase 1 Test Results filing (``scripts.file_test_results_backlog``).

Files each model's on-disk test evidence into the Test Results and Unit Test tabs,
sets the three test declarations honestly, and is idempotent on re-run.
"""
from __future__ import annotations

import pytest

from scripts import file_test_results_backlog as backlog
from src.governance.model_inventory import get_model, register_model, rebuild_inventory_view

MODEL_IDS = tuple(backlog.MODELS)


def _register_all():
    for mid in MODEL_IDS:
        register_model(model_id=mid, name=backlog.MODELS[mid][1], actor="test")
    rebuild_inventory_view()


def _fake_root(tmp_path):
    for _mid, (folder, _name, _intg) in backlog.MODELS.items():
        d = tmp_path / "docs" / "models" / folder
        d.mkdir(parents=True, exist_ok=True)
        (d / "test_results.pdf").write_bytes(b"%PDF-1.5 test results\n%%EOF")
    return tmp_path


def _data(mid):
    return get_model(mid)["data"]


def test_it_files_test_results_and_unit_test_on_every_model(tmp_path):
    _register_all()
    backlog.apply(phys_root=_fake_root(tmp_path))
    for mid in MODEL_IDS:
        cats = {d["category"] for d in _data(mid)["documents"]}
        assert "Test Results" in cats
        assert "Unit Test" in cats


def test_it_sets_test_declarations_honestly(tmp_path):
    _register_all()
    backlog.apply(phys_root=_fake_root(tmp_path))
    for mid in MODEL_IDS:
        d = _data(mid)
        assert d["unit_tests"] == "Yes"
        assert d["benchmark_tests"] == "No"          # never fabricated
        assert d["integration_tests"] == backlog.MODELS[mid][2]


@pytest.mark.parametrize("mid,expected", [("MKM-FIRE-001", "No"), ("MKM-SEIS-001", "No"),
                                          ("MKM-FC-001", "Yes"), ("MKM-DE-001", "Yes")])
def test_integration_flag_reflects_handover_presence(tmp_path, mid, expected):
    _register_all()
    backlog.apply(phys_root=_fake_root(tmp_path))
    assert _data(mid)["integration_tests"] == expected


def test_it_is_idempotent(tmp_path):
    root = _fake_root(tmp_path)
    _register_all()
    backlog.apply(phys_root=root)
    again = backlog.apply(phys_root=root)
    assert again == [
        {"model": mid, "fields": [], "documents": []} for mid in MODEL_IDS
    ]
