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

"""The MKM-EF-001 governance-record completion (``scripts.complete_ef001_governance``).

Fills the record gaps a completeness audit found. The properties worth
protecting: the blank scalar fields and empty histories are populated, the
validation-question upgrades are applied *honestly* (the not-done ones stay Not
Addressed), and a re-run is a no-op.
"""
from __future__ import annotations

from scripts import complete_ef001_governance as complete
from scripts import register_ef001
from src.governance.model_inventory import get_model, register_model, rebuild_inventory_view


def _register_ef001():
    for model_id, name in (("MKM-GH-001", "GEV Hazard"), ("MKM-PR-001", "PRS Pricing")):
        register_model(model_id=model_id, name=name, actor="test")
    rebuild_inventory_view()
    register_ef001.register()


def _data():
    return get_model("MKM-EF-001")["data"]


def test_it_fills_the_blank_scalar_fields():
    _register_ef001()
    complete.apply()
    d = _data()
    assert d["description"].startswith("The Event Frequency Model")
    assert d["validation_date"] == "2026-07-29"
    assert d["recertification_date"] == "2027-07-29"


def test_it_records_version_and_change_history():
    _register_ef001()
    complete.apply()
    d = _data()
    versions = {v["version"] for v in d["version_history"]}
    assert {"0.1.0", "1.0.0", "1.1.0"} <= versions
    assert len(d["change_history"]) >= 2


def test_the_validation_upgrades_are_honest():
    """Genuinely-done questions move up; benchmarking and independent validation
    stay Not Addressed because neither has happened."""
    _register_ef001()
    complete.apply()
    by_id = {q["item_id"]: q["status"] for q in _data()["validation_questions"]}
    assert by_id["VQ-003"] == "Addressed"
    assert by_id["VQ-004"] == "Addressed"
    assert by_id["VQ-002"] == "Partially Addressed"
    # The three that are genuinely not done must remain honest.
    assert by_id["VQ-008"] == "Not Addressed"   # no benchmark
    assert by_id["VQ-009"] == "Not Addressed"   # not independently validated


def test_it_is_idempotent():
    _register_ef001()
    complete.apply()
    again = complete.apply()
    assert again == {"fields": [], "versions": 0, "changes": 0, "questions": 0}


def test_it_does_not_overwrite_a_populated_field():
    """A description already set by a human is left intact."""
    _register_ef001()
    from src.governance.model_inventory import update_model_field
    update_model_field(model_id="MKM-EF-001", field="description",
                       value="hand-written", actor="test")
    rebuild_inventory_view()
    result = complete.apply()
    assert "description" not in result["fields"]
    assert _data()["description"] == "hand-written"
