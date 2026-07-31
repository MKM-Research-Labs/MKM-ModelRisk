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

"""The MKM-TC-001 governance-record completion (``scripts.complete_tc001_governance``).

Fills the blank dates and test declarations, adds a change history, records the
unassessed validation questions honestly, and files the existing test-results PDF
as Unit Test evidence.
"""
from __future__ import annotations

from scripts import complete_tc001_governance as complete
from src.governance.model_inventory import get_model, register_model, rebuild_inventory_view


def _register_tc001():
    """A freshly-registered TC-001 has the nine seeded questions and blank fields."""
    register_model(model_id="MKM-TC-001",
                   name="Tropical Cyclone Progression and Wind-Field", actor="test")
    rebuild_inventory_view()


def _fake_root(tmp_path):
    d = tmp_path / "docs" / "models" / "typhoon"
    d.mkdir(parents=True)
    (d / "test_results.pdf").write_bytes(b"%PDF-1.4 tc test results\n%%EOF")
    return tmp_path


def _data():
    return get_model("MKM-TC-001")["data"]


def test_it_sets_the_blank_dates_and_test_fields(tmp_path):
    _register_tc001()
    complete.apply(phys_root=_fake_root(tmp_path))
    d = _data()
    assert d["validation_date"] == "2026-05-27"
    assert d["recertification_date"] == "2027-05-27"
    assert d["unit_tests"] == "Yes"
    assert d["integration_tests"] == "Yes"
    assert d["benchmark_tests"] == "No"


def test_it_adds_change_history(tmp_path):
    _register_tc001()
    complete.apply(phys_root=_fake_root(tmp_path))
    versions = {c["version"] for c in _data()["change_history"]}
    assert {"0.6.0", "0.7.0"} <= versions


def test_it_files_the_unit_test_doc(tmp_path):
    _register_tc001()
    complete.apply(phys_root=_fake_root(tmp_path))
    cats = {d["category"] for d in _data()["documents"]}
    assert "Unit Test" in cats


def test_all_validation_questions_are_recorded_and_honest(tmp_path):
    _register_tc001()
    complete.apply(phys_root=_fake_root(tmp_path))
    by_id = {q["item_id"]: q for q in _data()["validation_questions"]}
    assert all(by_id[f"VQ-00{n}"]["rationale"] for n in range(1, 10))
    assert by_id["VQ-001"]["status"] == "Addressed"
    assert by_id["VQ-002"]["status"] == "Partially Addressed"
    assert by_id["VQ-003"]["status"] == "Addressed"
    # the genuinely-undone ones stay honest — not inflated to close the audit
    for undone in ("VQ-004", "VQ-005", "VQ-008", "VQ-009"):
        assert by_id[undone]["status"] == "Not Addressed"


def test_it_is_idempotent(tmp_path):
    root = _fake_root(tmp_path)
    _register_tc001()
    complete.apply(phys_root=root)
    again = complete.apply(phys_root=root)
    assert again == {"fields": [], "changes": 0, "questions": 0, "documents": []}
