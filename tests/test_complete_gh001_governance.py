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

"""The MKM-GH-001 governance-record completion (``scripts.complete_gh001_governance``).

Mirrors the EF-001 completion: fills blank test fields and validation date,
records the unassessed validation questions honestly, and files the existing
test-results PDF into the Test Results and Unit Test tabs.
"""
from __future__ import annotations

from scripts import complete_gh001_governance as complete
from src.governance.model_inventory import get_model, register_model, rebuild_inventory_view


def _register_gh001():
    """A freshly-registered GH-001 has the nine seeded questions and blank fields."""
    register_model(model_id="MKM-GH-001", name="GEV Hazard Curve Model", actor="test")
    rebuild_inventory_view()


def _fake_root(tmp_path):
    d = tmp_path / "docs" / "models" / "gev_hazard"
    d.mkdir(parents=True)
    (d / "test_results.pdf").write_bytes(b"%PDF-1.4 gh test results\n%%EOF")
    return tmp_path


def _data():
    return get_model("MKM-GH-001")["data"]


def test_it_sets_the_blank_test_fields_and_validation_date(tmp_path):
    _register_gh001()
    complete.apply(phys_root=_fake_root(tmp_path))
    d = _data()
    assert d["validation_date"] == "2026-02-13"
    assert d["unit_tests"] == "Yes"
    assert d["integration_tests"] == "Yes"


def test_it_files_the_test_evidence_docs(tmp_path):
    _register_gh001()
    complete.apply(phys_root=_fake_root(tmp_path))
    cats = {d["category"] for d in _data()["documents"]}
    assert "Test Results" in cats
    assert "Unit Test" in cats


def test_all_validation_questions_are_recorded_and_honest(tmp_path):
    _register_gh001()
    complete.apply(phys_root=_fake_root(tmp_path))
    by_id = {q["item_id"]: q for q in _data()["validation_questions"]}
    # every question now carries a rationale (none left blank)
    assert all(by_id[f"VQ-00{n}"]["rationale"] for n in range(1, 10))
    assert by_id["VQ-001"]["status"] == "Addressed"
    assert by_id["VQ-002"]["status"] == "Partially Addressed"
    # the genuinely-undone ones stay honest
    assert by_id["VQ-008"]["status"] == "Not Addressed"
    assert by_id["VQ-009"]["status"] == "Not Addressed"


def test_it_is_idempotent(tmp_path):
    root = _fake_root(tmp_path)
    _register_gh001()
    complete.apply(phys_root=root)
    again = complete.apply(phys_root=root)
    assert again == {"fields": [], "questions": 0, "documents": []}
