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

"""The PF-001/ST-001 governance-record completion (``scripts.complete_pf_st_governance``).

One parameterised pass over two identically-stated models: fills the blank test
declarations and validation date, records the seven unassessed validation
questions honestly, and files the existing test-results PDF into the Test Results
and Unit Test tabs. Sensitivity and Monitoring are deliberately left untouched.
"""
from __future__ import annotations

import pytest

from scripts import complete_pf_st_governance as complete
from src.governance.model_inventory import get_model, register_model, rebuild_inventory_view

MODEL_IDS = ("MKM-PF-001", "MKM-ST-001")


def _register_all():
    """Freshly-registered models have the nine seeded questions and blank fields."""
    for mid in MODEL_IDS:
        register_model(model_id=mid, name=complete.MODELS[mid]["name"], actor="test")
    rebuild_inventory_view()


def _fake_root(tmp_path):
    for mid in MODEL_IDS:
        d = tmp_path / complete.MODELS[mid]["folder"]
        d.mkdir(parents=True)
        (d / "test_results.pdf").write_bytes(b"%PDF-1.4 test results\n%%EOF")
    return tmp_path


def _data(mid):
    return get_model(mid)["data"]


@pytest.mark.parametrize("mid", MODEL_IDS)
def test_it_sets_the_blank_test_fields_and_validation_date(tmp_path, mid):
    _register_all()
    complete.apply(phys_root=_fake_root(tmp_path))
    d = _data(mid)
    assert d["validation_date"] == "2026-03-18"
    assert d["unit_tests"] == "Yes"
    assert d["integration_tests"] == "Yes"
    assert d["benchmark_tests"] == "No"


@pytest.mark.parametrize("mid", MODEL_IDS)
def test_it_files_the_test_evidence_docs(tmp_path, mid):
    _register_all()
    complete.apply(phys_root=_fake_root(tmp_path))
    cats = {d["category"] for d in _data(mid)["documents"]}
    assert "Test Results" in cats
    assert "Unit Test" in cats


@pytest.mark.parametrize("mid", MODEL_IDS)
def test_all_validation_questions_are_recorded_and_honest(tmp_path, mid):
    _register_all()
    complete.apply(phys_root=_fake_root(tmp_path))
    by_id = {q["item_id"]: q for q in _data(mid)["validation_questions"]}
    # every question now carries a rationale (none left blank)
    assert all(by_id[f"VQ-00{n}"]["rationale"] for n in range(1, 10))
    assert by_id["VQ-001"]["status"] == "Addressed"
    assert by_id["VQ-002"]["status"] == "Partially Addressed"
    assert by_id["VQ-003"]["status"] == "Addressed"
    # the genuinely-undone ones stay honest — not inflated to close the audit
    for undone in ("VQ-004", "VQ-005", "VQ-008", "VQ-009"):
        assert by_id[undone]["status"] == "Not Addressed"


def test_it_is_idempotent(tmp_path):
    root = _fake_root(tmp_path)
    _register_all()
    complete.apply(phys_root=root)
    again = complete.apply(phys_root=root)
    assert again == [
        {"model": mid, "fields": [], "questions": 0, "documents": []}
        for mid in MODEL_IDS
    ]
