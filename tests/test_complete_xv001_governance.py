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

"""The MKM-XV-001 governance-record completion (``scripts.complete_xv001_governance``).

Fills the gaps the completeness audit raised. The properties worth protecting:
the blank fields and empty collections are populated, the validation-question
upgrades are honest (data quality and independent validation stay Not
Addressed), nothing is recorded for work that has not happened, and a re-run is
a no-op.
"""
from __future__ import annotations

import pytest

from scripts import complete_xv001_governance as complete
from scripts import register_xv001
from src.governance.completeness import findings, scan
from src.governance.model_inventory import get_model, rebuild_inventory_view, register_model

pytestmark = pytest.mark.usefixtures("physicalrisk_groups")

_PDF = "docs/models/prs_xva/MKM-XV-001_model_document.pdf"


def _registered(tmp_path):
    for model_id, name in (("MKM-PR-001", "PRS Pricing"), ("MKM-EF-001", "Event Frequency"),
                           ("MKM-TD-001", "Trading Desk")):
        register_model(model_id=model_id, name=name, actor="test")
    rebuild_inventory_view()
    register_xv001.register()
    pdf = tmp_path / _PDF
    pdf.parent.mkdir(parents=True)
    pdf.write_bytes(b"%PDF-1.4 xva\n%%EOF")
    return tmp_path


def _data():
    return get_model("MKM-XV-001")["data"]


def _gaps():
    return {g["key"] for g in findings(scan("2026-10-19", model_ids=["MKM-XV-001"]))}


def test_it_fills_the_blank_fields_and_moves_to_v0_10(tmp_path):
    complete.apply(phys_root=_registered(tmp_path))
    d = _data()
    assert d["description"].startswith("The PRS XVA Model")
    assert d["vendor"] == "In-house"
    assert d["next_review_date"] == "2027-10-09"
    assert d["materiality_rationale"] and d["complexity_rationale"]
    assert d["version"] == "0.10.0"


def test_it_records_the_collections(tmp_path):
    complete.apply(phys_root=_registered(tmp_path))
    d = _data()
    assert {v["version"] for v in d["version_history"]} == {"0.9.0", "0.10.0"}
    assert len(d["data_sources"]) == 6
    assert len(d["evaluations"]) == 4
    assert {r["raci"] for r in d["raci_roles"]} >= {"Accountable", "Responsible"}
    assert len(d["fairness_assessments"]) == 1


def test_the_validation_upgrades_are_honest(tmp_path):
    complete.apply(phys_root=_registered(tmp_path))
    by_id = {q["item_id"]: q["status"] for q in _data()["validation_questions"]}
    assert by_id["VQ-003"] == by_id["VQ-004"] == "Addressed"
    assert by_id["VQ-006"] == by_id["VQ-007"] == "Addressed"
    assert by_id["VQ-001"] == by_id["VQ-002"] == by_id["VQ-008"] == "Partially Addressed"
    assert by_id["VQ-005"] == "Not Addressed"   # inputs are synthetic
    assert by_id["VQ-009"] == "Not Addressed"   # not independently validated


def test_nothing_is_recorded_for_work_not_done(tmp_path):
    """The validation, sign-off and review record stays empty, and the peer
    reviewer is left for the owner to name."""
    complete.apply(phys_root=_registered(tmp_path))
    d = _data()
    for field in ("validation_date", "last_review_date", "mrc_signoff_date",
                  "recertification_date", "peer_reviewer"):
        assert not d.get(field), field
    assert not d.get("signoff_history")


def test_it_closes_the_audited_gaps(tmp_path):
    root = _registered(tmp_path)
    before = _gaps()
    complete.apply(phys_root=root)
    closed = before - _gaps()
    assert closed >= {"description", "materiality_rationale", "complexity_rationale",
                      "vendor", "next_review_date", "data_sources", "evaluations", "raci_roles",
                      "fairness_assessments", "version_history",
                      "Analysis", "Convergence", "Calibration"}


def test_the_validation_questions_stay_a_partial_gap(tmp_path):
    """Four of nine questions are answered, so the finding narrows rather than closes."""
    complete.apply(phys_root=_registered(tmp_path))
    gap = next(g for g in findings(scan("2026-10-19", model_ids=["MKM-XV-001"]))
               if g["key"] == "validation_questions")
    assert gap["partial"] is True


def test_it_files_the_model_document_under_the_new_categories(tmp_path):
    summary = complete.apply(phys_root=_registered(tmp_path))
    assert [c for c, _ in summary["documents"]] == ["Analysis", "Convergence", "Calibration"]


def test_it_is_idempotent(tmp_path):
    root = _registered(tmp_path)
    complete.apply(phys_root=root)
    again = complete.apply(phys_root=root)
    assert again["fields"] == []
    assert set(again["items"].values()) == {0}
    assert again["questions"] == 0
    assert again["documents"] == []
    assert len(_data()["evaluations"]) == 4


def test_it_refuses_an_unregistered_model():
    with pytest.raises(RuntimeError):
        complete.apply()


def test_main_reports(tmp_path, monkeypatch, capsys):
    root = _registered(tmp_path)
    monkeypatch.setattr(complete.attach_xv001_docs, "PHYS_ROOT", root)
    monkeypatch.setattr(complete.attach_xv001_docs.apply, "__defaults__",
                        (complete.attach_xv001_docs.DOCS, root, None))
    assert complete.main() == 0
    assert "XV-001 record" in capsys.readouterr().out
